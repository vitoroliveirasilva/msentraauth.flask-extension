from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from flask import Flask
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import (
    AuthenticationRequired,
    AuthEvent,
    Identity,
    InvalidCallbackError,
    MemoryStorage,
    MicrosoftEntraAuth,
)
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalResult
from flask_ms_entra_auth.auth.token_cache import token_cache_key
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.context import get_current_identity
from flask_ms_entra_auth.web.session import WebSessionManager


class BrowserMsalClient:
    def __init__(self) -> None:
        self.cache: SerializableTokenCache | None = None
        self.state: str | None = None
        self.initiate_error: Exception | None = None
        self.complete_error: Exception | None = None
        self.flow_error: str | None = None
        self.token_result: MsalResult = {
            "id_token_claims": {
                "oid": "object-id",
                "tid": "tenant-id",
                "name": "Browser User",
                "preferred_username": "browser@example.com",
            }
        }
        self.accounts: Sequence[MsalAccount] = [
            {
                "home_account_id": "home-id",
                "local_account_id": "object-id",
                "realm": "tenant-id",
            }
        ]
        self.initiated: list[tuple[list[str], str, str]] = []
        self.completed: list[tuple[Mapping[str, object], Mapping[str, str]]] = []

    def initiate_auth_code_flow(
        self,
        scopes: list[str],
        *,
        redirect_uri: str,
        state: str,
    ) -> MsalResult:
        self.initiated.append((scopes, redirect_uri, state))
        self.state = state
        if self.initiate_error is not None:
            raise self.initiate_error
        if self.flow_error is not None:
            return {"error": self.flow_error}
        return {
            "auth_uri": (
                f"https://login.microsoftonline.com/tenant-id/oauth2/v2.0/authorize?state={state}"
            ),
            "state": state,
            "nonce": "nonce-value",
        }

    def acquire_token_by_auth_code_flow(
        self,
        auth_code_flow: Mapping[str, object],
        auth_response: Mapping[str, str],
    ) -> MsalResult:
        self.completed.append((auth_code_flow, auth_response))
        if self.complete_error is not None:
            raise self.complete_error
        if self.cache is not None:
            self.cache.has_state_changed = True
        return self.token_result

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
        del scopes, account, force_refresh
        return {"access_token": "silent-server-token"}


def make_app(
    *,
    auto_routes: bool = True,
    handle_errors: bool = True,
    secret_key: str | None = "test-secret",
    unauthenticated_mode: str = "redirect",
    url_prefix: str = "/auth",
    post_login: str = "/",
    post_logout: str = "/",
    storage: MemoryStorage | None = None,
) -> tuple[Flask, MicrosoftEntraAuth, BrowserMsalClient]:
    app = Flask("extension-web-test")
    app.testing = True
    app.secret_key = secret_key
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="client-secret",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE="extension-web",
        MS_ENTRA_AUTO_REGISTER_ROUTES=auto_routes,
        MS_ENTRA_HANDLE_ROUTE_ERRORS=handle_errors,
        MS_ENTRA_UNAUTHENTICATED_MODE=unauthenticated_mode,
        MS_ENTRA_URL_PREFIX=url_prefix,
        MS_ENTRA_POST_LOGIN_REDIRECT_URI=post_login,
        MS_ENTRA_POST_LOGOUT_REDIRECT_URI=post_logout,
    )
    msal_client = BrowserMsalClient()

    def factory(
        config: MicrosoftEntraAuthConfig,
        cache: SerializableTokenCache,
    ) -> BrowserMsalClient:
        assert config.tenant_id == "tenant-id"
        msal_client.cache = cache
        return msal_client

    extension = MicrosoftEntraAuth(
        storage=storage or MemoryStorage(),
        msal_client_factory=factory,
    )
    extension.init_app(app)
    return app, extension, msal_client


def add_protected_routes(app: Flask, extension: MicrosoftEntraAuth) -> None:
    @app.get("/protected")
    @extension.login_required
    def protected() -> str:
        return get_current_identity().object_id

    @app.get("/protected-explicit")
    @extension.login_required(on_missing="redirect")
    def protected_explicit() -> str:
        return get_current_identity().username or "missing"

    @app.get("/protected-raise")
    @extension.login_required(on_missing="raise")
    def protected_raise() -> str:
        return get_current_identity().object_id

    @app.post("/protected-post")
    @extension.login_required
    def protected_post() -> str:
        return "ok"


def pending_flow_id(app: Flask, client: Any) -> str:
    manager: WebSessionManager = app.extensions["ms_entra_auth"].web_session
    with client.session_transaction() as browser_session:
        metadata = browser_session[manager.session_key]
        flow_id = metadata["flow_id"]
        assert isinstance(flow_id, str)
        return flow_id


def begin_browser_login(client: Any, *, next_url: str = "/protected") -> tuple[str, str]:
    response = client.get("/auth/login", query_string={"next": next_url})
    assert response.status_code == 302
    location = response.headers["Location"]
    state = parse_qs(urlsplit(location).query)["state"][0]
    return location, state


def complete_browser_login(client: Any, state: str, *, expected: str = "/protected") -> None:
    response = client.get("/auth/callback", query_string={"code": "code", "state": state})
    assert response.status_code == 302
    assert response.headers["Location"] == expected


def test_complete_browser_flow_restores_identity_and_logout_clears_only_auth_state() -> None:
    backend = MemoryStorage()
    app, extension, msal_client = make_app(storage=backend)
    add_protected_routes(app, extension)
    client = app.test_client()

    protected = client.get("/protected?tab=1")
    assert protected.status_code == 302
    login_url = protected.headers["Location"]
    parsed_login = urlsplit(login_url)
    assert parsed_login.path == "/auth/login"
    assert parse_qs(parsed_login.query)["next"] == ["/protected?tab=1"]

    login = client.get(login_url)
    assert login.status_code == 302
    provider_url = login.headers["Location"]
    state = parse_qs(urlsplit(provider_url).query)["state"][0]
    assert msal_client.initiated[0][0] == ["User.Read"]

    callback = client.get(
        "/auth/callback",
        query_string={"code": "server-code", "state": state},
    )
    assert callback.status_code == 302
    assert callback.headers["Location"] == "/protected?tab=1"

    response = client.get("/protected")
    assert response.status_code == 200
    assert response.text == "object-id"
    assert client.get("/protected-explicit").text == "browser@example.com"

    manager: WebSessionManager = app.extensions["ms_entra_auth"].web_session
    with client.session_transaction() as browser_session:
        browser_session["application-value"] = "preserved"
        metadata = browser_session[manager.session_key]
        assert metadata.keys() == {"session_id"}
        serialized_cookie_state = repr(dict(browser_session))
        assert "object-id" not in serialized_cookie_state
        assert "browser@example.com" not in serialized_cookie_state
        assert "server-code" not in serialized_cookie_state

    state_storage = app.extensions["ms_entra_auth"].storage
    assert state_storage.load(token_cache_key("home-id")) == b"{}"

    logout = client.post("/auth/logout")
    assert logout.status_code == 302
    assert logout.headers["Location"] == "/"
    assert state_storage.load(token_cache_key("home-id")) is None
    with client.session_transaction() as browser_session:
        assert manager.session_key not in browser_session
        assert browser_session["application-value"] == "preserved"

    assert client.get("/protected").status_code == 302
    assert client.get("/auth/logout").status_code == 405


def test_callback_replay_and_duplicate_fields_are_rejected_without_500() -> None:
    app, _, _ = make_app()
    client = app.test_client()
    _, state = begin_browser_login(client)

    first = client.get("/auth/callback", query_string={"code": "code", "state": state})
    assert first.status_code == 302

    replay = client.get("/auth/callback", query_string={"code": "code", "state": state})
    assert replay.status_code == 400
    assert replay.text == "Authentication request is invalid or expired."

    begin_browser_login(client)
    duplicate = client.get("/auth/callback?state=x&state=y&code=z")
    assert duplicate.status_code == 400
    assert "invalid or expired" in duplicate.text


def test_cancelled_login_is_predictable_and_consumed() -> None:
    app, _, _ = make_app()
    client = app.test_client()
    _, state = begin_browser_login(client)

    response = client.get(
        "/auth/callback",
        query_string={"error": "access_denied", "state": state},
    )

    assert response.status_code == 400
    assert response.text == "Authentication was cancelled."
    assert (
        client.get(
            "/auth/callback",
            query_string={"error": "access_denied", "state": state},
        ).status_code
        == 400
    )


def test_route_error_handling_can_be_delegated_to_application() -> None:
    app, _, _ = make_app(handle_errors=False)
    client = app.test_client()

    with pytest.raises(InvalidCallbackError):
        client.get("/auth/callback", query_string={"state": "missing"})


def test_missing_secret_key_returns_safe_configuration_response() -> None:
    app, _, _ = make_app(secret_key=None)
    response = app.test_client().get("/auth/login")

    assert response.status_code == 500
    assert response.text == "Authentication is not configured correctly."


def test_invalid_next_url_and_provider_failure_return_safe_statuses() -> None:
    app, _, msal_client = make_app()
    client = app.test_client()

    invalid_next = client.get("/auth/login", query_string={"next": "https://evil.example.com"})
    assert invalid_next.status_code == 400

    msal_client.initiate_error = RuntimeError("raw-provider-secret")
    unavailable = client.get("/auth/login")
    assert unavailable.status_code == 503
    assert unavailable.text == "Authentication service is temporarily unavailable."
    assert "raw-provider-secret" not in unavailable.text


def test_login_replaces_and_deletes_previous_pending_flow() -> None:
    app, _, _ = make_app()
    client = app.test_client()

    begin_browser_login(client)
    first_flow = pending_flow_id(app, client)
    state_storage = app.extensions["ms_entra_auth"].storage
    assert state_storage.load(f"flow:{first_flow}") is not None

    begin_browser_login(client)
    second_flow = pending_flow_id(app, client)

    assert second_flow != first_flow
    assert state_storage.load(f"flow:{first_flow}") is None
    assert state_storage.load(f"flow:{second_flow}") is not None


def test_manual_route_registration_is_idempotent_and_honors_custom_prefix() -> None:
    app, extension, _ = make_app(auto_routes=False, url_prefix="/identity")
    assert "/identity/login" not in {rule.rule for rule in app.url_map.iter_rules()}

    extension.register_routes(app)
    extension.register_routes(app)

    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/identity/login" in rules
    assert "/identity/callback" in rules
    assert "/identity/logout" in rules


def test_register_routes_validates_application_state_and_blueprint_name() -> None:
    _app, extension, _ = make_app(auto_routes=False)
    invalid_app: Any = object()
    with pytest.raises(TypeError, match=r"flask\.Flask"):
        extension.register_routes(invalid_app)

    other = Flask("other")
    with pytest.raises(RuntimeError, match="not initialized"):
        extension.register_routes(other)

    collision, collision_extension, _ = make_app(auto_routes=False)
    from flask import Blueprint

    collision.register_blueprint(Blueprint("ms_entra_auth", __name__))
    with pytest.raises(RuntimeError, match="blueprint name"):
        collision_extension.register_routes(collision)


def test_login_required_raise_modes_and_unsafe_method_do_not_redirect() -> None:
    app, extension, _ = make_app()
    add_protected_routes(app, extension)
    client = app.test_client()

    with pytest.raises(AuthenticationRequired):
        client.get("/protected-raise")
    with pytest.raises(AuthenticationRequired):
        client.post("/protected-post")

    raised_app, raised_extension, _ = make_app(unauthenticated_mode="raise")
    add_protected_routes(raised_app, raised_extension)
    with pytest.raises(AuthenticationRequired):
        raised_app.test_client().get("/protected")


def test_login_required_rejects_invalid_mode_and_requires_registered_routes() -> None:
    _, extension, _ = make_app()
    with pytest.raises(ValueError, match="on_missing"):
        extension.login_required(on_missing="invalid")

    app, extension, _ = make_app(auto_routes=False)

    @app.get("/protected")
    @extension.login_required
    def protected() -> str:
        return "ok"

    with pytest.raises(RuntimeError, match="routes are not registered"):
        app.test_client().get("/protected")


def test_direct_api_uses_defaults_and_custom_redirects() -> None:
    app, extension, msal_client = make_app(
        post_login="/home",
        post_logout="/signed-out",
    )

    with app.test_request_context("/"):
        auth_uri = extension.begin_login()
        assert auth_uri.startswith("https://login.microsoftonline.com/")
        state = msal_client.state
        assert state is not None
        result = extension.complete_login({"code": "code", "state": state})
        assert result.next_url == "/home"
        assert get_current_identity().object_id == "object-id"
        assert extension.acquire_token() == "silent-server-token"
        assert extension.logout() == "/signed-out"


def test_extension_methods_require_current_initialized_application() -> None:
    _, extension, _ = make_app()

    with pytest.raises(RuntimeError):
        extension.begin_login()

    other = Flask("other-context")
    other.secret_key = "secret"
    with other.test_request_context("/"), pytest.raises(RuntimeError, match="not initialized"):
        extension.begin_login()


def test_begin_login_cleans_new_flow_when_cookie_reference_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, extension, _ = make_app()
    state = app.extensions["ms_entra_auth"]
    saved_flow_ids: list[str] = []
    original_begin = state.flow.begin_login

    def record_begin(*, next_url: str, scopes: Any = None) -> Any:
        started = original_begin(next_url=next_url, scopes=scopes)
        saved_flow_ids.append(started.flow_id)
        return started

    monkeypatch.setattr(
        type(state.flow), "begin_login", lambda self, **kwargs: record_begin(**kwargs)
    )

    def fail_set(self: WebSessionManager, flow_id: str) -> None:
        del self, flow_id
        raise RuntimeError("cookie write failed")

    monkeypatch.setattr(WebSessionManager, "set_pending_flow", fail_set)
    with (
        app.test_request_context("/"),
        pytest.raises(RuntimeError, match="cookie write failed"),
    ):
        extension.begin_login()

    assert saved_flow_ids
    assert state.storage.load(f"flow:{saved_flow_ids[0]}") is None


def test_logout_discards_pending_flow_without_identity() -> None:
    app, extension, _ = make_app()
    state = app.extensions["ms_entra_auth"]

    with app.test_request_context("/"):
        extension.begin_login()
        manager = state.web_session
        flow_id = manager.discard_pending_flow()
        assert flow_id is not None
        manager.set_pending_flow(flow_id)
        assert extension.logout() == "/"
        assert state.storage.load(f"flow:{flow_id}") is None


def test_extension_hook_decorators_integrate_with_login_logout_errors_and_events() -> None:
    app, extension, _ = make_app()
    client = app.test_client()
    calls: list[str] = []

    @extension.on_authenticated
    def authenticated(identity: Identity) -> None:
        calls.append(f"authenticated:{identity.object_id}")

    @extension.on_logout
    def logged_out(identity: Identity | None) -> None:
        calls.append(f"logout:{identity.object_id if identity else None}")

    @extension.on_error
    def errored(error: object) -> None:
        calls.append(f"error:{type(error).__name__}")

    @extension.on_event
    def evented(event: AuthEvent) -> None:
        calls.append(f"event:{event.name}")

    _, state = begin_browser_login(client)
    complete_browser_login(client, state)
    assert client.post("/auth/logout").status_code == 302
    assert client.get("/auth/callback").status_code == 400

    assert calls[:3] == [
        "event:authentication_started",
        "authenticated:object-id",
        "event:authentication_succeeded",
    ]
    assert "logout:object-id" in calls
    assert "event:logout_completed" in calls
    assert "error:InvalidCallbackError" in calls
    assert "event:authentication_error" in calls


def test_authenticated_hook_rejection_prevents_session_and_cleans_token_cache() -> None:
    from flask_ms_entra_auth import AuthenticationRejected

    app, extension, _ = make_app(handle_errors=True)
    client = app.test_client()

    @extension.on_authenticated
    def reject(identity: Identity) -> None:
        del identity
        raise AuthenticationRejected("disabled locally")

    _, state = begin_browser_login(client)
    response = client.get("/auth/callback", query_string={"code": "code", "state": state})
    assert response.status_code == 403
    assert response.text == "Authentication was rejected by the application."

    storage = app.extensions["ms_entra_auth"].storage
    assert storage.load(token_cache_key("home-id")) is None
    manager = app.extensions["ms_entra_auth"].web_session
    with client.session_transaction() as browser_session:
        assert manager.session_key not in browser_session


def test_cleanup_storage_failure_is_reported_without_replacing_hook_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from flask_ms_entra_auth import AuthenticationRejected, StorageError

    app, extension, _ = make_app(handle_errors=False)
    client = app.test_client()
    errors: list[str] = []
    extension.on_error(lambda error: errors.append(type(error).__name__))

    @extension.on_authenticated
    def reject(identity: Identity) -> None:
        del identity
        raise AuthenticationRejected("disabled locally")

    def fail_cleanup(storage: object, home_account_id: str) -> None:
        del storage, home_account_id
        raise StorageError("cleanup failed")

    monkeypatch.setattr("flask_ms_entra_auth.extension.delete_token_cache", fail_cleanup)
    _, state = begin_browser_login(client)
    with pytest.raises(AuthenticationRejected):
        client.get("/auth/callback", query_string={"code": "code", "state": state})

    assert errors == ["StorageError", "AuthenticationRejected"]


def test_logout_hook_failure_occurs_after_authentication_state_is_cleared() -> None:
    app, extension, _ = make_app(handle_errors=True)
    client = app.test_client()

    @extension.on_logout
    def broken(identity: Identity | None) -> None:
        assert identity is not None
        raise RuntimeError("private database failure")

    _, state = begin_browser_login(client)
    complete_browser_login(client, state)

    response = client.post("/auth/logout")
    assert response.status_code == 503
    assert response.text == "Authentication service is temporarily unavailable."

    manager = app.extensions["ms_entra_auth"].web_session
    with client.session_transaction() as browser_session:
        assert manager.session_key not in browser_session


@pytest.mark.parametrize("handle_errors", [True, False])
def test_before_request_storage_failure_is_sanitized_or_propagated(
    handle_errors: bool,
) -> None:
    from flask_ms_entra_auth import StorageError

    class RestoreFailingStorage(MemoryStorage):
        fail_load = False

        def load(self, key: str) -> bytes | None:
            if self.fail_load and ":identity:" in key:
                raise StorageError("restore failed")
            return super().load(key)

    backend = RestoreFailingStorage()
    app, extension, _ = make_app(storage=backend, handle_errors=handle_errors)
    add_protected_routes(app, extension)
    client = app.test_client()
    errors: list[str] = []
    extension.on_error(lambda error: errors.append(type(error).__name__))

    _, state = begin_browser_login(client)
    complete_browser_login(client, state)
    backend.fail_load = True

    if handle_errors:
        response = client.get("/protected")
        assert response.status_code == 503
        assert response.text == "Authentication service is temporarily unavailable."
    else:
        with pytest.raises(StorageError, match="restore failed"):
            client.get("/protected")

    assert errors == ["StorageError"]
