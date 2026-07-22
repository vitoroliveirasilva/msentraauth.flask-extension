from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

import pytest
from flask import Flask, session
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import (
    AuthenticationRequired,
    Identity,
    InvalidNavigationTarget,
    MemoryStorage,
    MicrosoftEntraAuth,
    StorageError,
)
from flask_ms_entra_auth.auth.flow import AuthCodeFlowService
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalResult
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.context import clear_identity, get_current_identity
from flask_ms_entra_auth.hooks import HookRegistry
from flask_ms_entra_auth.observability import Observability
from flask_ms_entra_auth.security import audit_security
from flask_ms_entra_auth.storage.namespaced import NamespacedStorage
from flask_ms_entra_auth.web.session import WebSessionManager
from flask_ms_entra_auth.web.urls import validate_next_url


def config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="residual-hardening",
        token_cache_ttl=300,
    )


def configured_app(name: str = "residual-hardening") -> Flask:
    app = Flask(name)
    app.testing = True
    app.secret_key = "x" * 32
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="client-secret",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE=f"{name}-namespace",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=True,
    )
    return app


class BeginMsalClient:
    def initiate_auth_code_flow(
        self,
        scopes: list[str],
        *,
        redirect_uri: str,
        state: str,
    ) -> MsalResult:
        del scopes, redirect_uri
        return {
            "auth_uri": (
                f"https://login.microsoftonline.com/tenant-id/oauth2/v2.0/authorize?state={state}"
            ),
            "state": state,
        }

    def acquire_token_by_auth_code_flow(
        self,
        auth_code_flow: Mapping[str, object],
        auth_response: Mapping[str, str],
    ) -> MsalResult:
        del auth_code_flow, auth_response
        raise AssertionError("completion is not expected")

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        del username
        return ()

    def acquire_token_silent_with_error(
        self,
        scopes: list[str],
        account: MsalAccount,
        *,
        force_refresh: bool = False,
    ) -> MsalResult | None:
        del scopes, account, force_refresh
        raise AssertionError("silent acquisition is not expected")


class RecordingStorage:
    def __init__(self, *, fail_delete: bool = False) -> None:
        self.values: dict[str, bytes] = {}
        self.fail_delete = fail_delete

    def load(self, key: str) -> bytes | None:
        return self.values.get(key)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del ttl
        self.values[key] = bytes(value)

    def delete(self, key: str) -> None:
        if self.fail_delete:
            raise StorageError("delete failed")
        self.values.pop(key, None)


def identity(*, object_id: str = "object-id") -> Identity:
    return Identity.from_claims(
        {"oid": object_id, "tid": "tenant-id"},
        home_account_id="home-id",
        expected_tenant_id="tenant-id",
    )


def test_security_audit_reports_debug_mode_as_error() -> None:
    app = configured_app("debug-audit")
    app.testing = False
    app.debug = True

    report = audit_security(
        app,
        config(),
        NamespacedStorage(MemoryStorage(), "debug-audit"),
    )

    debug_finding = next(
        finding for finding in report.findings if finding.code == "flask-debug-enabled"
    )
    assert debug_finding.severity == "error"
    assert report.passed is False


def test_non_ascii_request_id_is_replaced_with_generated_ascii_identifier() -> None:
    app = configured_app("request-id")
    observer = Observability(config(), HookRegistry(), logging.getLogger("request-id-test"))

    with app.test_request_context("/", headers={"X-Request-ID": "requisição-123"}):
        event = observer.emit("request")

    assert event.request_id is not None
    assert event.request_id != "requisição-123"
    assert event.request_id.isascii()


def test_navigation_target_rejects_ascii_delete_control_character() -> None:
    with pytest.raises(InvalidNavigationTarget, match="invalid"):
        validate_next_url("/account\x7fsettings", config())


def test_login_required_redirect_uses_authentication_security_headers() -> None:
    app = configured_app("protected-redirect")
    extension = MicrosoftEntraAuth()
    extension.init_app(app)

    @app.get("/protected")
    @extension.login_required
    def protected() -> str:
        return "protected"

    response = app.test_client().get("/protected?ticket=sensitive")

    assert response.status_code == 302
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_begin_login_preserves_cookie_error_when_flow_cleanup_also_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = configured_app("begin-cleanup")
    client = BeginMsalClient()

    def factory(
        resolved_config: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> BeginMsalClient:
        del resolved_config, cache
        return client

    extension = MicrosoftEntraAuth(msal_client_factory=factory)
    extension.init_app(app)

    def fail_session_write(self: WebSessionManager, flow_id: str) -> None:
        del self, flow_id
        raise RuntimeError("cookie write failed")

    def fail_flow_cleanup(self: AuthCodeFlowService, flow_id: str) -> None:
        del self, flow_id
        raise StorageError("flow cleanup failed")

    monkeypatch.setattr(WebSessionManager, "set_pending_flow", fail_session_write)
    monkeypatch.setattr(AuthCodeFlowService, "discard", fail_flow_cleanup)

    with app.test_request_context("/"), pytest.raises(RuntimeError) as captured:
        extension.begin_login()

    assert str(captured.value) == "cookie write failed"
    assert getattr(captured.value, "__notes__", []) == [
        "new authentication flow cleanup also failed",
    ]


def test_logout_clears_identity_before_pending_flow_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = configured_app("logout-order")
    extension = MicrosoftEntraAuth()
    extension.init_app(app)
    state = app.extensions["ms_entra_auth"]

    def fail_flow_cleanup(self: AuthCodeFlowService, flow_id: str) -> None:
        del self, flow_id
        raise StorageError("flow cleanup failed")

    monkeypatch.setattr(AuthCodeFlowService, "discard", fail_flow_cleanup)

    with app.test_request_context("/"):
        state.web_session.establish_identity(identity())
        state.web_session.set_pending_flow("pending-flow")

        with pytest.raises(StorageError, match="flow cleanup failed"):
            extension.logout()

        with pytest.raises(AuthenticationRequired):
            get_current_identity()
        assert state.web_session.restore_identity() is None


def test_identity_payload_is_removed_when_session_metadata_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = configured_app("metadata-cleanup")
    app.extensions["ms_entra_auth"] = object()
    storage = RecordingStorage()
    manager = WebSessionManager(config(), storage)
    calls = 0

    def fail_once(self: WebSessionManager, metadata: Mapping[str, str]) -> None:
        nonlocal calls
        del self, metadata
        calls += 1
        if calls == 1:
            raise RuntimeError("session metadata write failed")

    monkeypatch.setattr(WebSessionManager, "_write_metadata", fail_once)

    with app.test_request_context("/"), pytest.raises(RuntimeError, match="metadata write"):
        manager.establish_identity(identity())

    assert storage.values == {}
    assert calls == 2


def test_metadata_write_failure_preserves_previous_authenticated_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = configured_app("metadata-rollback")
    app.extensions["ms_entra_auth"] = object()
    storage = RecordingStorage()
    manager = WebSessionManager(config(), storage)
    original_write = WebSessionManager._write_metadata
    calls = 0

    with app.test_request_context("/"):
        previous_identity = identity()
        manager.establish_identity(previous_identity)
        previous_metadata = dict(session[manager.session_key])
        previous_values = dict(storage.values)

        def fail_once(self: WebSessionManager, metadata: Mapping[str, str]) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("session metadata write failed")
            original_write(self, metadata)

        monkeypatch.setattr(WebSessionManager, "_write_metadata", fail_once)

        with pytest.raises(RuntimeError, match="metadata write"):
            manager.establish_identity(identity(object_id="replacement"))

        assert dict(session[manager.session_key]) == previous_metadata
        assert storage.values == previous_values
        assert get_current_identity() == previous_identity


def test_rotation_without_request_binding_replaces_previous_session() -> None:
    app = configured_app("unbound-rotation")
    app.extensions["ms_entra_auth"] = object()
    storage = RecordingStorage()
    manager = WebSessionManager(config(), storage)

    with app.test_request_context("/"):
        manager.establish_identity(identity())
        previous_keys = set(storage.values)
        clear_identity()

        replacement = identity(object_id="replacement")
        manager.establish_identity(replacement)

        assert get_current_identity() == replacement
        assert len(storage.values) == 1
        assert set(storage.values).isdisjoint(previous_keys)


def test_identity_cleanup_failures_do_not_mask_metadata_write_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = configured_app("metadata-cleanup-failures")
    app.extensions["ms_entra_auth"] = object()
    storage = RecordingStorage(fail_delete=True)
    manager = WebSessionManager(config(), storage)

    def fail_metadata(self: WebSessionManager, metadata: Mapping[str, str]) -> None:
        del self, metadata
        raise RuntimeError("session metadata write failed")

    def fail_clear_identity() -> None:
        raise RuntimeError("request identity cleanup failed")

    monkeypatch.setattr(WebSessionManager, "_write_metadata", fail_metadata)
    monkeypatch.setattr(
        "flask_ms_entra_auth.web.session.clear_identity",
        fail_clear_identity,
    )

    with app.test_request_context("/"), pytest.raises(RuntimeError) as captured:
        manager.establish_identity(identity())

    assert str(captured.value) == "session metadata write failed"
    assert getattr(captured.value, "__notes__", []) == [
        "authentication session metadata cleanup also failed",
        "new identity cleanup also failed",
        "request identity cleanup also failed",
    ]
    assert storage.values
