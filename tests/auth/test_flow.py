from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import pytest
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import (
    AuthenticationCancelled,
    IdentityValidationError,
    InvalidCallbackError,
    MemoryStorage,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from flask_ms_entra_auth.auth import flow as flow_module
from flask_ms_entra_auth.auth.flow import AuthCodeFlowService
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalResult
from flask_ms_entra_auth.auth.token_cache import token_cache_key
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig


class RecordingStorage(MemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self.saved: list[tuple[str, bytes, int | None]] = []
        self.deleted: list[str] = []

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        self.saved.append((key, value, ttl))
        super().save(key, value, ttl=ttl)

    def take(self, key: str) -> bytes | None:
        self.deleted.append(key)
        return super().take(key)

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        super().delete(key)


class FakeInteractiveClient:
    def __init__(self) -> None:
        self.flow_result: MsalResult | object = {
            "auth_uri": "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/authorize",
            "state": "unused",
            "nonce": "nonce-value",
        }
        self.token_result: MsalResult | object = {
            "id_token_claims": {
                "oid": "object-id",
                "tid": "tenant-id",
                "name": "Test User",
            }
        }
        self.accounts: Sequence[MsalAccount] = [
            {
                "home_account_id": "home-id",
                "local_account_id": "object-id",
                "realm": "tenant-id",
            }
        ]
        self.initiate_error: Exception | None = None
        self.complete_error: Exception | None = None
        self.accounts_error: Exception | None = None
        self.mutate_cache = False
        self.cache: SerializableTokenCache | None = None
        self.initiate_calls: list[tuple[list[str], str, str]] = []
        self.complete_calls: list[tuple[Mapping[str, object], Mapping[str, str]]] = []

    def initiate_auth_code_flow(
        self,
        scopes: list[str],
        *,
        redirect_uri: str,
        state: str,
    ) -> MsalResult:
        self.initiate_calls.append((scopes, redirect_uri, state))
        if self.initiate_error is not None:
            raise self.initiate_error
        if isinstance(self.flow_result, dict):
            result = dict(self.flow_result)
            if result.get("state") == "unused":
                result["state"] = state
            return result
        return self.flow_result  # type: ignore[return-value]

    def acquire_token_by_auth_code_flow(
        self,
        auth_code_flow: Mapping[str, object],
        auth_response: Mapping[str, str],
    ) -> MsalResult:
        self.complete_calls.append((auth_code_flow, auth_response))
        if self.mutate_cache and self.cache is not None:
            self.cache.has_state_changed = True
        if self.complete_error is not None:
            raise self.complete_error
        return self.token_result  # type: ignore[return-value]

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        assert username is None
        if self.accounts_error is not None:
            raise self.accounts_error
        return self.accounts


def config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="app",
        token_cache_ttl=7200,
        flow_ttl=600,
    )


def service_with_client(
    client: FakeInteractiveClient,
    *,
    storage: RecordingStorage | None = None,
) -> tuple[AuthCodeFlowService, RecordingStorage, list[SerializableTokenCache]]:
    backend = storage or RecordingStorage()
    caches: list[SerializableTokenCache] = []

    def factory(
        resolved: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> FakeInteractiveClient:
        assert resolved == config()
        caches.append(cache)
        client.cache = cache
        return client

    return (
        AuthCodeFlowService(config=config(), storage=backend, client_factory=factory),
        backend,
        caches,
    )


def begin_and_state(
    service: AuthCodeFlowService,
    storage: RecordingStorage,
    *,
    next_url: str = "/dashboard",
) -> tuple[str, str]:
    started = service.begin_login(next_url=next_url)
    payload = json.loads(storage.load(f"flow:{started.flow_id}").decode())  # type: ignore[union-attr]
    return started.flow_id, payload["flow"]["state"]


def test_begin_login_uses_scopes_redirect_state_and_server_side_ttl() -> None:
    client = FakeInteractiveClient()
    service, storage, caches = service_with_client(client)

    started = service.begin_login(
        next_url="/dashboard",
        scopes=[" Mail.Read ", "Mail.Read", "User.Read"],
    )

    assert started.auth_uri.startswith("https://login.microsoftonline.com/")
    assert client.initiate_calls[0][0] == ["Mail.Read", "User.Read"]
    assert client.initiate_calls[0][1] == config().redirect_uri
    assert client.initiate_calls[0][2]
    assert len(caches) == 1
    key, payload, ttl = storage.saved[-1]
    assert key == f"flow:{started.flow_id}"
    assert ttl == 600
    decoded = json.loads(payload)
    assert decoded["version"] == 1
    assert decoded["next_url"] == "/dashboard"
    assert decoded["flow"]["state"] == client.initiate_calls[0][2]


@pytest.mark.parametrize("scopes", ["User.Read", [123]])
def test_begin_login_validates_scope_container_and_entries(scopes: object) -> None:
    service, _, _ = service_with_client(FakeInteractiveClient())

    with pytest.raises(TypeError, match="scope"):
        service.begin_login(next_url="/", scopes=scopes)  # type: ignore[arg-type]


@pytest.mark.parametrize("scopes", [[], [""], ["   "]])
def test_begin_login_requires_at_least_one_non_empty_scope(scopes: list[str]) -> None:
    service, _, _ = service_with_client(FakeInteractiveClient())

    with pytest.raises(ValueError, match=r"scope|at least"):
        service.begin_login(next_url="/", scopes=scopes)


def test_begin_login_factory_or_client_failure_is_sanitized() -> None:
    storage = RecordingStorage()

    def broken_factory(config: object, cache: object) -> Any:
        del config, cache
        raise RuntimeError("secret-provider-detail")

    service = AuthCodeFlowService(config=config(), storage=storage, client_factory=broken_factory)
    with pytest.raises(ProviderUnavailableError) as raised:
        service.begin_login(next_url="/")
    assert "secret-provider-detail" not in str(raised.value)

    client = FakeInteractiveClient()
    client.initiate_error = RuntimeError("raw-network-detail")
    service, _, _ = service_with_client(client)
    with pytest.raises(ProviderUnavailableError) as raised:
        service.begin_login(next_url="/")
    assert "raw-network-detail" not in str(raised.value)


@pytest.mark.parametrize(
    ("flow_result", "match"),
    [
        (object(), "invalid authentication flow"),
        ({"error": "invalid_request", "correlation_id": "abc-123"}, "could not be started"),
        ({"auth_uri": "https://login.microsoftonline.com/x", "state": "wrong"}, "inconsistent"),
        ({"auth_uri": 123, "state": "unused"}, "authorization URI"),
        (
            {"auth_uri": "http://login.microsoftonline.com/x", "state": "unused"},
            "authorization URI",
        ),
        (
            {"auth_uri": "https://user@login.microsoftonline.com/x", "state": "unused"},
            "authorization URI",
        ),
        (
            {"auth_uri": "https://login.microsoftonline.com:bad/x", "state": "unused"},
            "authorization URI",
        ),
        ({"auth_uri": "https://[invalid", "state": "unused"}, "authorization URI"),
        ({"auth_uri": "https://evil.example.com/x", "state": "unused"}, "unexpected"),
    ],
)
def test_begin_login_rejects_invalid_msal_flow(flow_result: object, match: str) -> None:
    client = FakeInteractiveClient()
    client.flow_result = flow_result
    service, _, _ = service_with_client(client)

    with pytest.raises(TokenAcquisitionError, match=match):
        service.begin_login(next_url="/")


def test_begin_login_rejects_non_json_or_deep_flow_data() -> None:
    client = FakeInteractiveClient()
    client.flow_result = {
        "auth_uri": "https://login.microsoftonline.com/x",
        "state": "unused",
        "bad": object(),
    }
    service, _, _ = service_with_client(client)
    with pytest.raises(StorageError, match="invalid data"):
        service.begin_login(next_url="/")

    nested: object = "end"
    for _ in range(14):
        nested = {"x": nested}
    client.flow_result = {
        "auth_uri": "https://login.microsoftonline.com/x",
        "state": "unused",
        "deep": nested,
    }
    with pytest.raises(StorageError, match="deeply nested"):
        service.begin_login(next_url="/")


def test_begin_login_wraps_json_serialization_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, _ = service_with_client(FakeInteractiveClient())

    def fail(*args: object, **kwargs: object) -> str:
        del args, kwargs
        raise ValueError("raw-flow-secret")

    monkeypatch.setattr(flow_module, "json", SimpleNamespace(dumps=fail))
    with pytest.raises(StorageError, match="could not be serialized") as raised:
        service.begin_login(next_url="/")
    assert "raw-flow-secret" not in str(raised.value)


def test_complete_login_consumes_flow_builds_identity_and_persists_changed_cache() -> None:
    client = FakeInteractiveClient()
    client.mutate_cache = True
    service, storage, caches = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)

    result = service.complete_login(
        flow_id=flow_id,
        auth_response={"code": "server-code", "state": state},
    )

    assert result.identity.object_id == "object-id"
    assert result.identity.home_account_id == "home-id"
    assert result.next_url == "/dashboard"
    assert storage.load(f"flow:{flow_id}") is None
    assert f"flow:{flow_id}" in storage.deleted
    assert client.complete_calls[0][1] == {"code": "server-code", "state": state}
    assert len(caches) == 2
    assert storage.load(token_cache_key("home-id")) == b"{}"
    assert storage.saved[-1][2] == 7200


def test_complete_login_does_not_persist_unchanged_cache() -> None:
    client = FakeInteractiveClient()
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)
    writes_before = len(storage.saved)

    service.complete_login(flow_id=flow_id, auth_response={"code": "code", "state": state})

    assert len(storage.saved) == writes_before


@pytest.mark.parametrize("flow_id", ["", "bad/value", "x" * 129, 123])
def test_complete_login_rejects_invalid_flow_identifier(flow_id: object) -> None:
    service, _, _ = service_with_client(FakeInteractiveClient())

    with pytest.raises(InvalidCallbackError, match="identifier"):
        service.complete_login(flow_id=flow_id, auth_response={})  # type: ignore[arg-type]


def test_complete_login_rejects_missing_expired_or_consumed_flow() -> None:
    service, _, _ = service_with_client(FakeInteractiveClient())

    with pytest.raises(InvalidCallbackError, match="missing, expired, or consumed"):
        service.complete_login(flow_id="missing", auth_response={})


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (b"not-json", "could not be decoded"),
        (b"[]", "invalid structure"),
        (json.dumps({"version": 2, "flow": {}, "next_url": "/"}).encode(), "invalid structure"),
        (json.dumps({"version": 1, "flow": [], "next_url": "/"}).encode(), "invalid structure"),
        (json.dumps({"version": 1, "flow": {}, "next_url": 1}).encode(), "invalid structure"),
    ],
)
def test_complete_login_rejects_corrupt_stored_flow(payload: bytes, match: str) -> None:
    storage = RecordingStorage()
    storage.save("flow:stored", payload, ttl=600)
    service, _, _ = service_with_client(FakeInteractiveClient(), storage=storage)

    with pytest.raises(StorageError, match=match):
        service.complete_login(flow_id="stored", auth_response={})
    assert storage.load("flow:stored") is None


@pytest.mark.parametrize(
    "response",
    [
        object(),
        {str(index): "x" for index in range(33)},
        {1: "value"},
        {"": "value"},
        {"x" * 129: "value"},
        {"state": 123},
        {"state": "x" * 8193},
        {"bad\nkey": "value"},
    ],
)
def test_complete_login_validates_callback_shape(response: object) -> None:
    client = FakeInteractiveClient()
    service, storage, _ = service_with_client(client)
    flow_id, _ = begin_and_state(service, storage)

    with pytest.raises(InvalidCallbackError, match="invalid structure"):
        service.complete_login(flow_id=flow_id, auth_response=response)  # type: ignore[arg-type]


def test_complete_login_requires_matching_state_and_consumes_before_failure() -> None:
    service, storage, _ = service_with_client(FakeInteractiveClient())
    flow_id, _ = begin_and_state(service, storage)

    with pytest.raises(InvalidCallbackError, match="state"):
        service.complete_login(flow_id=flow_id, auth_response={"state": "wrong"})

    assert storage.load(f"flow:{flow_id}") is None
    with pytest.raises(InvalidCallbackError, match="missing, expired, or consumed"):
        service.complete_login(flow_id=flow_id, auth_response={"state": "wrong"})


def test_cancelled_callback_is_predictable_and_provider_error_is_sanitized() -> None:
    service, storage, _ = service_with_client(FakeInteractiveClient())
    flow_id, state = begin_and_state(service, storage)
    with pytest.raises(AuthenticationCancelled, match="cancelled"):
        service.complete_login(
            flow_id=flow_id,
            auth_response={"error": "access_denied", "state": state},
        )

    flow_id, state = begin_and_state(service, storage)
    with pytest.raises(TokenAcquisitionError) as raised:
        service.complete_login(
            flow_id=flow_id,
            auth_response={
                "error": "invalid_grant",
                "error_description": "raw secret description",
                "correlation_id": "abc-123",
                "state": state,
            },
        )
    assert raised.value.code == "invalid_grant"
    assert raised.value.correlation_id == "abc-123"
    assert "raw secret" not in str(raised.value)


def test_complete_login_wraps_callback_validation_and_provider_failures() -> None:
    client = FakeInteractiveClient()
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)
    client.complete_error = ValueError("csrf raw state")
    with pytest.raises(InvalidCallbackError, match="validation failed") as raised:
        service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})
    assert "csrf raw" not in str(raised.value)

    flow_id, state = begin_and_state(service, storage)
    client.complete_error = RuntimeError("network raw detail")
    with pytest.raises(ProviderUnavailableError) as provider_error:
        service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})
    assert "network raw" not in str(provider_error.value)


@pytest.mark.parametrize(
    ("result", "error_type", "match"),
    [
        (object(), InvalidCallbackError, "invalid authentication result"),
        ({"error": "invalid_grant", "correlation_id": "abc"}, TokenAcquisitionError, "failed"),
        ({}, InvalidCallbackError, "identity claims"),
        ({"id_token_claims": []}, InvalidCallbackError, "identity claims"),
        (
            {"id_token_claims": {"name": "Incomplete"}},
            InvalidCallbackError,
            "account could not be resolved",
        ),
    ],
)
def test_complete_login_validates_provider_result(
    result: object,
    error_type: type[Exception],
    match: str,
) -> None:
    client = FakeInteractiveClient()
    client.token_result = result
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)

    with pytest.raises(error_type, match=match):
        service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})


@pytest.mark.parametrize(
    "accounts",
    [
        [],
        [
            {"home_account_id": "one", "local_account_id": "object-id", "realm": "tenant-id"},
            {"home_account_id": "two", "local_account_id": "object-id", "realm": "tenant-id"},
        ],
        [{"home_account_id": "home-id", "local_account_id": 123, "realm": "tenant-id"}],
        [{"home_account_id": "home-id", "local_account_id": "object-id", "realm": 123}],
        [{"home_account_id": "", "local_account_id": "object-id", "realm": "tenant-id"}],
    ],
)
def test_complete_login_requires_one_exact_valid_account(accounts: Sequence[MsalAccount]) -> None:
    client = FakeInteractiveClient()
    client.accounts = accounts
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)

    with pytest.raises(InvalidCallbackError, match="account could not be resolved"):
        service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})


def test_account_tenant_id_alias_is_supported() -> None:
    client = FakeInteractiveClient()
    client.accounts = [
        {
            "home_account_id": "home-id",
            "local_account_id": "object-id",
            "tenant_id": "tenant-id",
        }
    ]
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)

    result = service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})

    assert result.identity.home_account_id == "home-id"


def test_identity_tenant_mismatch_remains_identity_validation_error() -> None:
    client = FakeInteractiveClient()
    client.token_result = {"id_token_claims": {"oid": "object-id", "tid": "other-tenant"}}
    client.accounts = [
        {
            "home_account_id": "home-id",
            "local_account_id": "object-id",
            "realm": "other-tenant",
        }
    ]
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)

    with pytest.raises(IdentityValidationError, match="configured tenant"):
        service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})


def test_account_lookup_failure_is_provider_unavailable() -> None:
    client = FakeInteractiveClient()
    client.accounts_error = RuntimeError("raw-account-error")
    service, storage, _ = service_with_client(client)
    flow_id, state = begin_and_state(service, storage)

    with pytest.raises(ProviderUnavailableError) as provider_error:
        service.complete_login(flow_id=flow_id, auth_response={"state": state, "code": "x"})

    assert "raw-account-error" not in str(provider_error.value)


def test_discard_is_idempotent_and_validates_identifier() -> None:
    service, storage, _ = service_with_client(FakeInteractiveClient())
    flow_id, _ = begin_and_state(service, storage)

    service.discard(flow_id)
    service.discard(flow_id)
    assert storage.load(f"flow:{flow_id}") is None

    with pytest.raises(InvalidCallbackError, match="identifier"):
        service.discard("bad/value")


def test_safe_metadata_discards_unsafe_empty_long_and_non_string_values() -> None:
    assert flow_module._safe_metadata("valid_code") == "valid_code"
    assert flow_module._safe_metadata(123) is None
    assert flow_module._safe_metadata("   ") is None
    assert flow_module._safe_metadata("x" * 65) is None
    assert flow_module._safe_metadata("bad value") is None


def test_json_compatibility_accepts_lists_tuples_and_scalars() -> None:
    flow_module._ensure_json_compatible(
        {"none": None, "list": [1, "x"], "tuple": (True, 1.5), "mapping": {"x": "y"}}
    )

    with pytest.raises(StorageError, match="invalid data"):
        flow_module._ensure_json_compatible({1: "bad"})


class NonAtomicFlowStorage:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def load(self, key: str) -> bytes | None:
        return self.values.get(key)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del ttl
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.values.pop(key, None)


def test_complete_login_supports_non_atomic_storage_compatibility_path() -> None:
    backend = NonAtomicFlowStorage()
    client = FakeInteractiveClient()

    def factory(
        resolved: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> FakeInteractiveClient:
        del resolved
        client.cache = cache
        return client

    service = AuthCodeFlowService(config=config(), storage=backend, client_factory=factory)
    started = service.begin_login(next_url="/")
    payload = json.loads(backend.load(f"flow:{started.flow_id}").decode())  # type: ignore[union-attr]
    state = payload["flow"]["state"]

    result = service.complete_login(
        flow_id=started.flow_id,
        auth_response={"code": "code", "state": state},
    )

    assert result.identity.object_id == "object-id"
    assert backend.deleted == [f"flow:{started.flow_id}"]


def test_non_atomic_storage_missing_flow_does_not_attempt_delete() -> None:
    backend = NonAtomicFlowStorage()
    client = FakeInteractiveClient()

    def factory(
        resolved: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> FakeInteractiveClient:
        del resolved, cache
        return client

    service = AuthCodeFlowService(config=config(), storage=backend, client_factory=factory)

    with pytest.raises(InvalidCallbackError, match="missing, expired, or consumed"):
        service.complete_login(
            flow_id="valid-flow-id",
            auth_response={"code": "code", "state": "state"},
        )

    assert backend.deleted == []
