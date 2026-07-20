from __future__ import annotations

import json
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest
from flask import Flask, session

from flask_ms_entra_auth import (
    AuthenticationRequired,
    ConfigurationError,
    Identity,
    InvalidCallbackError,
    MemoryStorage,
    MicrosoftEntraAuth,
    StorageError,
)
from flask_ms_entra_auth.context import get_current_identity
from flask_ms_entra_auth.web import session as session_module
from flask_ms_entra_auth.web.session import WebSessionManager


def create_app(*, secret_key: str | None = "test-secret") -> tuple[Flask, MicrosoftEntraAuth]:
    app = Flask("web-session-test")
    app.secret_key = secret_key
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="client-secret",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE="session-tests",
        MS_ENTRA_AUTO_REGISTER_ROUTES=False,
        MS_ENTRA_IDENTITY_TTL=3600,
    )
    extension = MicrosoftEntraAuth(storage=MemoryStorage())
    extension.init_app(app)
    return app, extension


def identity(*, object_id: str = "object-id", tenant_id: str = "tenant-id") -> Identity:
    return Identity.from_claims(
        {
            "oid": object_id,
            "tid": tenant_id,
            "name": "Test User",
            "nested": {"groups": ["a", "b"]},
        },
        home_account_id=f"home-{object_id}",
        expected_tenant_id=tenant_id,
    )


def state_for(app: Flask) -> Any:
    return app.extensions["ms_entra_auth"]


def test_session_key_is_stable_and_does_not_expose_namespace() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    assert manager.session_key.startswith("_msentra_")
    assert "session-tests" not in manager.session_key
    assert manager.session_key == state_for(app).web_session.session_key


def test_secure_session_is_required_before_web_authentication() -> None:
    app, _ = create_app(secret_key=None)
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"), pytest.raises(ConfigurationError, match="SECRET_KEY"):
        manager.require_secure_session()


def test_pending_flow_is_stored_and_consumed_exactly_once() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        manager.set_pending_flow("flow_123")
        assert session[manager.session_key] == {"flow_id": "flow_123"}
        assert manager.consume_pending_flow() == "flow_123"
        assert manager.session_key not in session
        with pytest.raises(InvalidCallbackError, match="missing or already consumed"):
            manager.consume_pending_flow()


def test_discard_pending_flow_handles_present_and_absent_values() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        assert manager.discard_pending_flow() is None
        manager.set_pending_flow("flow-abc")
        assert manager.discard_pending_flow() == "flow-abc"
        assert manager.discard_pending_flow() is None


def test_invalid_pending_flow_identifier_is_rejected() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        session[manager.session_key] = {"flow_id": "bad/value"}
        with pytest.raises(InvalidCallbackError, match="reference is invalid"):
            manager.consume_pending_flow()


def test_establish_identity_rotates_reference_and_binds_current_request() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session
    first = identity(object_id="first")
    second = identity(object_id="second")

    with app.test_request_context("/"):
        session["other"] = "preserved"
        manager.establish_identity(first)
        first_metadata = dict(session[manager.session_key])
        assert first_metadata.keys() == {"session_id"}
        assert get_current_identity().object_id == "first"

        manager.establish_identity(second)
        second_metadata = dict(session[manager.session_key])
        assert second_metadata.keys() == {"session_id"}
        assert second_metadata != first_metadata
        assert get_current_identity().object_id == "second"
        assert session["other"] == "preserved"

        old_key = session_module._identity_key(first_metadata["session_id"])
        assert state_for(app).storage.load(old_key) is None


def test_establish_identity_rejects_wrong_type() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"), pytest.raises(TypeError, match="Identity"):
        manager.establish_identity(object())  # type: ignore[arg-type]


def test_restore_identity_returns_none_without_reference_and_clears_request_value() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        manager.establish_identity(identity())
        assert get_current_identity().object_id == "object-id"
        session.pop(manager.session_key)

        assert manager.restore_identity() is None
        with pytest.raises(AuthenticationRequired, match="authentication is required"):
            get_current_identity()


def test_restore_identity_removes_invalid_or_expired_reference() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        session[manager.session_key] = {"session_id": "bad/value"}
        assert manager.restore_identity() is None
        assert manager.session_key not in session

        session[manager.session_key] = {"session_id": "valid-id"}
        assert manager.restore_identity() is None
        assert manager.session_key not in session


def test_clear_authentication_removes_valid_reference_without_payload() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        session[manager.session_key] = {"session_id": "missing-payload"}

        assert manager.clear_authentication() is None
        assert manager.session_key not in session


def test_restore_identity_rebuilds_deeply_immutable_claims() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        manager.establish_identity(identity())
        manager.restore_identity()

        restored = get_current_identity()
        nested = restored.claims["nested"]
        assert isinstance(nested, MappingProxyType)
        assert nested["groups"] == ("a", "b")
        with pytest.raises(TypeError):
            restored.claims["oid"] = "changed"  # type: ignore[index]


def test_clear_authentication_deletes_only_extension_state_and_returns_identity() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        session["other"] = "kept"
        manager.establish_identity(identity())
        metadata = dict(session[manager.session_key])

        removed = manager.clear_authentication()

        assert removed is not None
        assert removed.object_id == "object-id"
        assert manager.session_key not in session
        assert session["other"] == "kept"
        assert (
            state_for(app).storage.load(session_module._identity_key(metadata["session_id"]))
            is None
        )
        assert manager.clear_authentication() is None


def _store_raw_identity(app: Flask, payload: bytes, session_id: str = "raw-id") -> None:
    manager: WebSessionManager = state_for(app).web_session
    session[manager.session_key] = {"session_id": session_id}
    state_for(app).storage.save(session_module._identity_key(session_id), payload, ttl=3600)


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (b"not-json", "could not be decoded"),
        (b"[]", "invalid structure"),
        (json.dumps({"claims": []}).encode(), "invalid claims"),
        (
            json.dumps(
                {
                    "object_id": 123,
                    "tenant_id": "tenant-id",
                    "home_account_id": "home",
                    "claims": {"oid": "object", "tid": "tenant-id"},
                }
            ).encode(),
            "invalid structure",
        ),
        (
            json.dumps(
                {
                    "object_id": "",
                    "tenant_id": "tenant-id",
                    "home_account_id": "home",
                    "claims": {"oid": "object", "tid": "tenant-id"},
                }
            ).encode(),
            "failed validation",
        ),
        (
            json.dumps(
                {
                    "object_id": "object",
                    "tenant_id": "other-tenant",
                    "home_account_id": "home",
                    "claims": {"oid": "object", "tid": "other-tenant"},
                }
            ).encode(),
            "another tenant",
        ),
    ],
)
def test_corrupt_stored_identity_fails_safely(payload: bytes, match: str) -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    with app.test_request_context("/"):
        _store_raw_identity(app, payload)
        with pytest.raises(StorageError, match=match):
            manager.restore_identity()


def test_optional_stored_identity_fields_must_be_strings_when_present() -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session
    payload = json.dumps(
        {
            "object_id": "object",
            "tenant_id": "tenant-id",
            "home_account_id": "home",
            "subject": 123,
            "claims": {"oid": "object", "tid": "tenant-id"},
        }
    ).encode()

    with app.test_request_context("/"):
        _store_raw_identity(app, payload)
        with pytest.raises(StorageError, match="invalid structure"):
            manager.restore_identity()


def test_identity_serialization_failure_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    app, _ = create_app()
    manager: WebSessionManager = state_for(app).web_session

    def fail(*args: object, **kwargs: object) -> str:
        del args, kwargs
        raise TypeError("raw-secret")

    monkeypatch.setattr(session_module, "json", SimpleNamespace(dumps=fail))
    with (
        app.test_request_context("/"),
        pytest.raises(StorageError, match="could not be serialized") as raised,
    ):
        manager.establish_identity(identity())

    assert "raw-secret" not in str(raised.value)


def test_thaw_json_value_handles_mapping_tuple_and_scalar() -> None:
    value = MappingProxyType({"items": (1, MappingProxyType({"ok": True}))})

    assert session_module._thaw_json_value(value) == {"items": [1, {"ok": True}]}
    assert session_module._thaw_json_value("value") == "value"
