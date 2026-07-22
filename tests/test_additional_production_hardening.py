from __future__ import annotations

from collections.abc import Callable, Sequence
from types import SimpleNamespace
from typing import cast

import pytest
from flask import Flask, session
from msal import SerializableTokenCache  # type: ignore[import-untyped]
from werkzeug.wrappers import Response as WerkzeugResponse

from flask_ms_entra_auth import (
    Identity,
    MemoryStorage,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from flask_ms_entra_auth.auth import token_cache as token_cache_module
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalClient, MsalResult
from flask_ms_entra_auth.auth.service import MsalService
from flask_ms_entra_auth.auth.token_cache import load_token_cache, persist_token_cache
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.context import get_current_identity
from flask_ms_entra_auth.web import session as session_module
from flask_ms_entra_auth.web.routes import _safe_error_response, _secure_redirect
from flask_ms_entra_auth.web.session import WebSessionManager


def _config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="additional-production-hardening",
        token_cache_ttl=7_200,
        flow_ttl=600,
        identity_ttl=7_200,
    )


def _identity(*, object_id: str = "object-id") -> Identity:
    return Identity.from_claims(
        {"oid": object_id, "tid": "tenant-id"},
        home_account_id=f"home-{object_id}",
        expected_tenant_id="tenant-id",
    )


def _assert_auth_response_headers(response: WerkzeugResponse) -> None:
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_auth_redirects_and_errors_disable_caching_and_referrer_leakage() -> None:
    app = Flask("response-hardening")

    with app.test_request_context("/"):
        redirect_response = _secure_redirect("/after-login")
        error_response = _safe_error_response(TokenAcquisitionError("internal detail"))

    assert redirect_response.status_code == 302
    assert redirect_response.headers["Location"] == "/after-login"
    assert error_response.status_code == 502
    _assert_auth_response_headers(redirect_response)
    _assert_auth_response_headers(error_response)


def test_token_cache_rejects_oversized_payload_before_deserialization() -> None:
    storage = MemoryStorage()
    storage.save(
        token_cache_module.token_cache_key("home-id"),
        b"x" * (token_cache_module._MAX_TOKEN_CACHE_PAYLOAD_BYTES + 1),
    )

    with pytest.raises(StorageError, match="supported storage size"):
        load_token_cache(storage, "home-id")


def test_token_cache_rejects_oversized_serialization_before_storage() -> None:
    class OversizedCache:
        has_state_changed = True

        def serialize(self) -> str:
            return "x" * (token_cache_module._MAX_TOKEN_CACHE_PAYLOAD_BYTES + 1)

    storage = RecordingStorage()
    cache = cast(SerializableTokenCache, OversizedCache())

    with pytest.raises(StorageError, match="supported storage size"):
        persist_token_cache(storage, "home-id", cache, ttl=3_600)

    assert storage.saved == []


def test_token_cache_rejects_non_text_serialization_safely() -> None:
    class InvalidCache:
        has_state_changed = True

        def serialize(self) -> object:
            return b"not-text"

    cache = cast(SerializableTokenCache, InvalidCache())

    with pytest.raises(StorageError, match="could not be serialized") as raised:
        persist_token_cache(MemoryStorage(), "home-id", cache, ttl=3_600)

    assert isinstance(raised.value.__cause__, TypeError)
    assert "not-text" not in str(raised.value)


class RecordingStorage(MemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self.saved: list[tuple[str, bytes, int | None]] = []

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        self.saved.append((key, value, ttl))
        super().save(key, value, ttl=ttl)


class FixedClock:
    def __init__(self, value: object) -> None:
        self.value = value

    def __call__(self) -> float:
        return cast(float, self.value)


@pytest.mark.parametrize("clock_value", [float("nan"), float("inf"), -float("inf"), True, "bad"])
def test_memory_storage_rejects_invalid_clock_values(clock_value: object) -> None:
    storage = MemoryStorage(clock=FixedClock(clock_value))

    with pytest.raises(StorageError, match="expiration calculation") as raised:
        storage.save("key", b"value", ttl=1)

    assert isinstance(raised.value.__cause__, ValueError)


def test_identity_rotation_preserves_existing_session_when_serialization_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = Flask("identity-rotation-hardening")
    app.secret_key = "s" * 32
    app.extensions["ms_entra_auth"] = object()
    storage = MemoryStorage()
    manager = WebSessionManager(_config(), storage)
    first_identity = _identity(object_id="first")
    replacement_identity = _identity(object_id="replacement")

    with app.test_request_context("/"):
        manager.establish_identity(first_identity)
        previous_metadata = dict(session[manager.session_key])
        previous_key = session_module._identity_key(previous_metadata["session_id"])
        previous_payload = storage.load(previous_key)

        def fail_serialization(*args: object, **kwargs: object) -> str:
            del args, kwargs
            raise TypeError("sensitive serialization detail")

        monkeypatch.setattr(session_module, "json", SimpleNamespace(dumps=fail_serialization))

        with pytest.raises(StorageError, match="could not be serialized"):
            manager.establish_identity(replacement_identity)

        assert dict(session[manager.session_key]) == previous_metadata
        assert storage.load(previous_key) == previous_payload
        assert get_current_identity() == first_identity


class FailingSaveStorage(MemoryStorage):
    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del key, value, ttl
        raise StorageError("safe persistence failure")


class CacheMutatingClient:
    def __init__(
        self,
        cache: SerializableTokenCache,
        *,
        result: MsalResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self._cache = cache
        self._result = {"access_token": "token"} if result is None else result
        self._error = error

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        assert username is None
        return ({"home_account_id": "home-id"},)

    def acquire_token_silent_with_error(
        self,
        scopes: list[str],
        account: MsalAccount,
        *,
        force_refresh: bool = False,
    ) -> MsalResult | None:
        del scopes, account, force_refresh
        self._cache.has_state_changed = True
        if self._error is not None:
            raise self._error
        return self._result


def _service(
    storage: MemoryStorage,
    client_builder: Callable[[SerializableTokenCache], MsalClient],
) -> MsalService:
    def factory(
        config: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> MsalClient:
        assert config == _config()
        return client_builder(cache)

    return MsalService(_config(), storage, factory)


def _notes(error: BaseException) -> list[str]:
    return cast(list[str], getattr(error, "__notes__", []))


def test_provider_error_is_not_masked_by_cache_persistence_failure() -> None:
    raw_error = RuntimeError("provider detail")
    service = _service(
        FailingSaveStorage(),
        lambda cache: cast(MsalClient, CacheMutatingClient(cache, error=raw_error)),
    )

    with pytest.raises(ProviderUnavailableError) as raised:
        service.acquire_token_silent(home_account_id="home-id")

    assert raised.value.__cause__ is raw_error
    assert _notes(raised.value) == ["token cache persistence also failed"]


def test_token_error_is_not_masked_by_cache_persistence_failure() -> None:
    service = _service(
        FailingSaveStorage(),
        lambda cache: cast(
            MsalClient,
            CacheMutatingClient(cache, result={"error": "invalid_grant"}),
        ),
    )

    with pytest.raises(TokenAcquisitionError) as raised:
        service.acquire_token_silent(home_account_id="home-id")

    assert raised.value.code == "invalid_grant"
    assert _notes(raised.value) == ["token cache persistence also failed"]


def test_cache_persistence_failure_still_fails_a_successful_token_acquisition() -> None:
    service = _service(
        FailingSaveStorage(),
        lambda cache: cast(MsalClient, CacheMutatingClient(cache)),
    )

    with pytest.raises(StorageError, match="safe persistence failure"):
        service.acquire_token_silent(home_account_id="home-id")


class FailOnReplacementStorage(MemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self._save_count = 0

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        self._save_count += 1
        if self._save_count == 2:
            raise StorageError("replacement persistence failed")
        super().save(key, value, ttl=ttl)


def test_identity_rotation_preserves_existing_session_when_new_storage_write_fails() -> None:
    app = Flask("identity-rotation-storage-hardening")
    app.secret_key = "s" * 32
    app.extensions["ms_entra_auth"] = object()
    storage = FailOnReplacementStorage()
    manager = WebSessionManager(_config(), storage)
    first_identity = _identity(object_id="first")

    with app.test_request_context("/"):
        manager.establish_identity(first_identity)
        previous_metadata = dict(session[manager.session_key])
        previous_key = session_module._identity_key(previous_metadata["session_id"])
        previous_payload = storage.load(previous_key)

        with pytest.raises(StorageError, match="replacement persistence failed"):
            manager.establish_identity(_identity(object_id="replacement"))

        assert dict(session[manager.session_key]) == previous_metadata
        assert storage.load(previous_key) == previous_payload
        assert get_current_identity() == first_identity
