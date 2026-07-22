from __future__ import annotations

from collections.abc import Mapping

import pytest
from flask import Flask, session
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import (
    Identity,
    IdentityValidationError,
    InvalidNavigationTarget,
    MemoryStorage,
    StorageError,
)
from flask_ms_entra_auth.auth import flow as flow_module
from flask_ms_entra_auth.auth.flow import AuthCodeFlowService
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.web import session as session_module
from flask_ms_entra_auth.web.session import WebSessionManager


def config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="production-hardening",
        token_cache_ttl=7_200,
        flow_ttl=600,
        identity_ttl=7_200,
    )


def identity(*, claims: Mapping[str, object] | None = None) -> Identity:
    return Identity(
        object_id="object-id",
        tenant_id="tenant-id",
        home_account_id="home-id",
        claims={"oid": "object-id", "tid": "tenant-id"} if claims is None else claims,
    )


def test_identity_rejects_credentials_at_any_nesting_level() -> None:
    claims = {
        "oid": "object-id",
        "tid": "tenant-id",
        "profile": {"private": [{"Refresh_Token": "must-not-survive"}]},
    }

    with pytest.raises(IdentityValidationError, match="must not contain credentials"):
        Identity.from_claims(claims, home_account_id="home-id")


def test_identity_rejects_empty_nested_claim_names() -> None:
    claims = {"oid": "object-id", "tid": "tenant-id", "nested": {"": "invalid"}}

    with pytest.raises(IdentityValidationError, match="non-empty strings"):
        Identity.from_claims(claims, home_account_id="home-id")


def test_identity_rejects_excessive_nesting_and_non_finite_numbers() -> None:
    nested: object = "value"
    for _ in range(13):
        nested = {"nested": nested}

    with pytest.raises(IdentityValidationError, match="too deeply nested"):
        identity(claims={"oid": "object-id", "tid": "tenant-id", "nested": nested})

    with pytest.raises(IdentityValidationError, match="finite numeric"):
        identity(claims={"oid": "object-id", "tid": "tenant-id", "score": float("nan")})

    assert (
        identity(claims={"oid": "object-id", "tid": "tenant-id", "score": 1.5}).claims["score"]
        == 1.5
    )


def test_begin_login_rejects_unsafe_target_before_calling_provider() -> None:
    called = False

    def factory(
        _config: MicrosoftEntraAuthConfig,
        _cache: SerializableTokenCache,
    ) -> object:
        nonlocal called
        called = True
        return object()

    service = AuthCodeFlowService(
        config=config(),
        storage=MemoryStorage(),
        client_factory=factory,
    )

    with pytest.raises(InvalidNavigationTarget):
        service.begin_login(next_url="https://attacker.example/after-login")

    assert called is False


def test_complete_login_revalidates_target_loaded_from_storage() -> None:
    storage = MemoryStorage()
    flow_id = "valid-flow-id"
    payload = flow_module._serialize_flow(
        {
            "auth_uri": "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/authorize",
            "state": "expected-state",
        },
        next_url="https://attacker.example/after-login",
    )
    storage.save(f"flow:{flow_id}", payload, ttl=600)

    def factory(
        _config: MicrosoftEntraAuthConfig,
        _cache: SerializableTokenCache,
    ) -> object:
        raise AssertionError("provider must not be called for a tampered target")

    service = AuthCodeFlowService(
        config=config(),
        storage=storage,
        client_factory=factory,
    )

    with pytest.raises(StorageError, match="invalid navigation target"):
        service.complete_login(
            flow_id=flow_id,
            auth_response={"state": "expected-state", "code": "authorization-code"},
        )

    assert storage.load(f"flow:{flow_id}") is None


def test_flow_payload_limits_and_numeric_validation() -> None:
    oversized_flow = {
        "auth_uri": "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/authorize",
        "state": "state",
        "padding": "x" * flow_module._MAX_FLOW_PAYLOAD_BYTES,
    }

    with pytest.raises(StorageError, match="supported storage size"):
        flow_module._serialize_flow(oversized_flow, next_url="/")

    with pytest.raises(StorageError, match="supported storage size"):
        flow_module._deserialize_flow(b"x" * (flow_module._MAX_FLOW_PAYLOAD_BYTES + 1))

    with pytest.raises(StorageError, match="invalid numeric"):
        flow_module._ensure_json_compatible(float("inf"))

    flow_module._ensure_json_compatible(1.5)


def test_session_cleanup_tolerates_invalid_internal_references() -> None:
    app = Flask(__name__)
    app.secret_key = "s" * 32
    app.extensions["ms_entra_auth"] = object()
    manager = WebSessionManager(config(), MemoryStorage())

    with app.test_request_context("/"):
        session[manager.session_key] = {"flow_id": "inválido"}
        assert manager.discard_pending_flow() is None
        assert manager.session_key not in session

        session[manager.session_key] = {"session_id": "inválido"}
        assert manager.clear_authentication() is None
        assert manager.session_key not in session


def test_establish_identity_recovers_from_invalid_previous_reference() -> None:
    app = Flask(__name__)
    app.secret_key = "s" * 32
    app.extensions["ms_entra_auth"] = object()
    storage = MemoryStorage()
    manager = WebSessionManager(config(), storage)

    with app.test_request_context("/"):
        session[manager.session_key] = {"session_id": "inválido"}
        manager.establish_identity(identity())

        metadata = session[manager.session_key]
        assert isinstance(metadata, dict)
        new_session_id = metadata["session_id"]
        assert isinstance(new_session_id, str)
        assert storage.load(session_module._identity_key(new_session_id)) is not None


def test_corrupt_identity_clears_browser_reference_on_restore_and_logout() -> None:
    app = Flask(__name__)
    app.secret_key = "s" * 32
    app.extensions["ms_entra_auth"] = object()
    storage = MemoryStorage()
    manager = WebSessionManager(config(), storage)

    with app.test_request_context("/"):
        session_id = "valid-session-id"
        storage.save(session_module._identity_key(session_id), b"{", ttl=600)
        session[manager.session_key] = {"session_id": session_id}

        with pytest.raises(StorageError, match="could not be decoded"):
            manager.restore_identity()
        assert manager.session_key not in session

        storage.save(session_module._identity_key(session_id), b"{", ttl=600)
        session[manager.session_key] = {"session_id": session_id}

        with pytest.raises(StorageError, match="could not be decoded"):
            manager.clear_authentication()
        assert manager.session_key not in session


def test_identity_payload_size_is_bounded_before_storage_or_decoding() -> None:
    oversized_identity = identity(
        claims={
            "oid": "object-id",
            "tid": "tenant-id",
            "padding": "x" * session_module._MAX_IDENTITY_PAYLOAD_BYTES,
        }
    )

    with pytest.raises(StorageError, match="supported storage size"):
        session_module._serialize_identity(oversized_identity)

    with pytest.raises(StorageError, match="supported storage size"):
        session_module._deserialize_identity(
            b"x" * (session_module._MAX_IDENTITY_PAYLOAD_BYTES + 1),
            expected_tenant_id="tenant-id",
        )
