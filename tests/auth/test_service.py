from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import pytest
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import (
    AuthenticationRequired,
    ConsentRequired,
    MemoryStorage,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalResult
from flask_ms_entra_auth.auth.service import MsalService
from flask_ms_entra_auth.auth.token_cache import token_cache_key
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig


def config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="app",
        token_cache_ttl=7200,
    )


class FakeClient:
    def __init__(
        self,
        *,
        accounts: Sequence[MsalAccount] | None = None,
        result: MsalResult | None = None,
        error: Exception | None = None,
        mutate_cache: SerializableTokenCache | None = None,
    ) -> None:
        self.accounts = accounts if accounts is not None else [{"home_account_id": "home-id"}]
        self.result: MsalResult | None = (
            result if result is not None else {"access_token": "server-token"}
        )
        self.error = error
        self.mutate_cache = mutate_cache
        self.calls: list[tuple[list[str], MsalAccount, bool]] = []

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        assert username is None
        return self.accounts

    def acquire_token_silent_with_error(
        self,
        scopes: list[str],
        account: MsalAccount,
        *,
        force_refresh: bool = False,
    ) -> MsalResult | None:
        self.calls.append((scopes, account, force_refresh))
        if self.mutate_cache is not None:
            self.mutate_cache.has_state_changed = True
        if self.error is not None:
            raise self.error
        return self.result


def service_with_client(
    client_builder: Callable[[SerializableTokenCache], FakeClient],
    *,
    storage: MemoryStorage | None = None,
) -> tuple[MsalService, MemoryStorage, list[SerializableTokenCache]]:
    backend = storage or MemoryStorage()
    caches: list[SerializableTokenCache] = []

    def factory(
        resolved_config: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> FakeClient:
        assert resolved_config == config()
        caches.append(cache)
        return client_builder(cache)

    return MsalService(config(), backend, factory), backend, caches


def test_silent_acquisition_uses_default_scopes_and_matching_account() -> None:
    client = FakeClient()
    service, _, _ = service_with_client(lambda cache: client)

    token = service.acquire_token_silent(home_account_id="home-id")

    assert token == "server-token"
    assert client.calls == [(["User.Read"], {"home_account_id": "home-id"}, False)]


def test_custom_scopes_are_trimmed_deduplicated_and_force_refresh_is_forwarded() -> None:
    client = FakeClient()
    service, _, _ = service_with_client(lambda cache: client)

    token = service.acquire_token_silent(
        home_account_id="home-id",
        scopes=[" Mail.Read ", "Mail.Read", "User.Read"],
        force_refresh=True,
    )

    assert token == "server-token"
    assert client.calls[0][0] == ["Mail.Read", "User.Read"]
    assert client.calls[0][2] is True


@pytest.mark.parametrize("scopes", ["User.Read", [123]])
def test_runtime_scopes_require_non_string_iterable_of_strings(scopes: object) -> None:
    service, _, _ = service_with_client(lambda cache: FakeClient())
    invalid: Any = scopes

    with pytest.raises(TypeError, match="scope"):
        service.acquire_token_silent(home_account_id="home-id", scopes=invalid)


@pytest.mark.parametrize("scopes", [[], [""], ["   "]])
def test_runtime_scopes_require_at_least_one_non_empty_value(scopes: list[str]) -> None:
    service, _, _ = service_with_client(lambda cache: FakeClient())

    with pytest.raises(ValueError, match=r"scope|at least"):
        service.acquire_token_silent(home_account_id="home-id", scopes=scopes)


def test_force_refresh_must_be_boolean() -> None:
    service, _, _ = service_with_client(lambda cache: FakeClient())
    invalid: Any = 1

    with pytest.raises(TypeError, match="force_refresh"):
        service.acquire_token_silent(home_account_id="home-id", force_refresh=invalid)


def test_missing_matching_account_requires_authentication() -> None:
    service, _, _ = service_with_client(
        lambda cache: FakeClient(accounts=[{"home_account_id": "other"}])
    )

    with pytest.raises(AuthenticationRequired, match="no matching MSAL account"):
        service.acquire_token_silent(home_account_id="home-id")


def test_non_string_account_identifier_is_ignored() -> None:
    service, _, _ = service_with_client(
        lambda cache: FakeClient(accounts=[{"home_account_id": 123}])
    )

    with pytest.raises(AuthenticationRequired):
        service.acquire_token_silent(home_account_id="home-id")


def test_empty_cache_result_requires_interaction() -> None:
    service, _, _ = service_with_client(lambda cache: FakeClient(result={}))

    with pytest.raises(TokenAcquisitionError, match="no access token"):
        service.acquire_token_silent(home_account_id="home-id")


def test_explicit_none_result_requires_consent() -> None:
    def builder(cache: SerializableTokenCache) -> FakeClient:
        client = FakeClient()
        client.result = None
        return client

    service, _, _ = service_with_client(builder)

    with pytest.raises(ConsentRequired, match="interactive authentication"):
        service.acquire_token_silent(home_account_id="home-id")


def test_provider_error_result_is_sanitized_and_preserves_safe_metadata() -> None:
    service, _, _ = service_with_client(
        lambda cache: FakeClient(
            result={
                "error": "invalid_grant",
                "correlation_id": "abc-123",
                "error_description": "secret",
            }
        )
    )

    with pytest.raises(TokenAcquisitionError, match="silent token acquisition failed") as captured:
        service.acquire_token_silent(home_account_id="home-id")

    assert captured.value.code == "invalid_grant"
    assert captured.value.correlation_id == "abc-123"
    assert "secret" not in str(captured.value)


def test_unsafe_provider_metadata_is_discarded() -> None:
    service, _, _ = service_with_client(
        lambda cache: FakeClient(
            result={
                "error": "unsafe error with spaces",
                "correlation_id": "x" * 129,
            }
        )
    )

    with pytest.raises(TokenAcquisitionError) as captured:
        service.acquire_token_silent(home_account_id="home-id")

    assert captured.value.code is None
    assert captured.value.correlation_id is None


def test_non_string_metadata_is_discarded() -> None:
    service, _, _ = service_with_client(
        lambda cache: FakeClient(result={"error": 123, "correlation_id": object()})
    )

    with pytest.raises(TokenAcquisitionError) as captured:
        service.acquire_token_silent(home_account_id="home-id")

    assert captured.value.code is None
    assert captured.value.correlation_id is None


def test_invalid_result_shape_is_rejected() -> None:
    def builder(cache: SerializableTokenCache) -> FakeClient:
        client = FakeClient()
        client.result = ["invalid"]  # type: ignore[assignment]
        return client

    service, _, _ = service_with_client(builder)

    with pytest.raises(TokenAcquisitionError, match="invalid token result"):
        service.acquire_token_silent(home_account_id="home-id")


@pytest.mark.parametrize("token", [None, "", 123])
def test_access_token_must_be_non_empty_string(token: object) -> None:
    service, _, _ = service_with_client(lambda cache: FakeClient(result={"access_token": token}))

    with pytest.raises(TokenAcquisitionError, match="no access token"):
        service.acquire_token_silent(home_account_id="home-id")


def test_factory_failure_becomes_provider_unavailable_without_raw_message() -> None:
    raw_error = RuntimeError("provider-secret")

    def factory(config: MicrosoftEntraAuthConfig, cache: SerializableTokenCache) -> FakeClient:
        del config, cache
        raise raw_error

    service = MsalService(config(), MemoryStorage(), factory)

    with pytest.raises(ProviderUnavailableError, match="provider is unavailable") as captured:
        service.acquire_token_silent(home_account_id="home-id")

    assert captured.value.__cause__ is raw_error
    assert "provider-secret" not in str(captured.value)


def test_client_failure_becomes_provider_unavailable() -> None:
    raw_error = RuntimeError("network-secret")
    service, _, _ = service_with_client(lambda cache: FakeClient(error=raw_error))

    with pytest.raises(ProviderUnavailableError) as captured:
        service.acquire_token_silent(home_account_id="home-id")

    assert captured.value.__cause__ is raw_error


def test_changed_cache_is_persisted_after_success() -> None:
    def builder(cache: SerializableTokenCache) -> FakeClient:
        return FakeClient(mutate_cache=cache)

    service, storage, _ = service_with_client(builder)

    assert service.acquire_token_silent(home_account_id="home-id") == "server-token"
    assert storage.load(token_cache_key("home-id")) == b"{}"


def test_changed_cache_is_persisted_even_when_result_requires_interaction() -> None:
    def builder(cache: SerializableTokenCache) -> FakeClient:
        client = FakeClient(mutate_cache=cache)
        client.result = None
        return client

    service, storage, _ = service_with_client(builder)

    with pytest.raises(ConsentRequired):
        service.acquire_token_silent(home_account_id="home-id")

    assert storage.load(token_cache_key("home-id")) == b"{}"


def test_existing_cache_is_loaded_before_factory_receives_it() -> None:
    storage = MemoryStorage()
    storage.save(token_cache_key("home-id"), b"{}")
    service, _, caches = service_with_client(lambda cache: FakeClient(), storage=storage)

    service.acquire_token_silent(home_account_id="home-id")

    assert len(caches) == 1
    assert caches[0].serialize() == "{}"


def test_storage_failure_is_not_misclassified_as_provider_failure() -> None:
    class BrokenStorage(MemoryStorage):
        def load(self, key: str) -> bytes | None:
            del key
            raise StorageError("safe storage failure")

    service, _, _ = service_with_client(lambda cache: FakeClient(), storage=BrokenStorage())

    with pytest.raises(StorageError, match="safe storage failure"):
        service.acquire_token_silent(home_account_id="home-id")
