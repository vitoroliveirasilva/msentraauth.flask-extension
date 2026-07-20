from __future__ import annotations

from collections.abc import Sequence

import pytest
from flask import Flask
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import AuthenticationRequired, Identity, MicrosoftEntraAuth
from flask_ms_entra_auth.auth.protocols import MsalAccount, MsalResult
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.context import bind_identity

_VALID_CONFIG = {
    "MS_ENTRA_CLIENT_ID": "client-id",
    "MS_ENTRA_CLIENT_SECRET": "unit-test-secret",
    "MS_ENTRA_TENANT_ID": "tenant-id",
    "MS_ENTRA_REDIRECT_URI": "http://localhost/auth/callback",
}


class Client:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], bool]] = []

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        assert username is None
        return [{"home_account_id": "home-id"}]

    def acquire_token_silent_with_error(
        self,
        scopes: list[str],
        account: MsalAccount,
        *,
        force_refresh: bool = False,
    ) -> MsalResult | None:
        assert account["home_account_id"] == "home-id"
        self.calls.append((scopes, force_refresh))
        return {"access_token": "server-only-token"}


def create_app(name: str = "token") -> Flask:
    app = Flask(name)
    app.config.from_mapping(_VALID_CONFIG)
    return app


def identity() -> Identity:
    return Identity(object_id="oid", tenant_id="tenant-id", home_account_id="home-id")


def test_acquire_token_uses_current_identity_and_server_side_msal_service() -> None:
    client = Client()

    def factory(config: MicrosoftEntraAuthConfig, cache: SerializableTokenCache) -> Client:
        assert config.client_id == "client-id"
        assert cache.serialize() == "{}"
        return client

    extension = MicrosoftEntraAuth(msal_client_factory=factory)
    app = create_app()
    extension.init_app(app)

    with app.test_request_context("/"):
        bind_identity(identity())
        token = extension.acquire_token(["Mail.Read"], force_refresh=True)

    assert token == "server-only-token"
    assert client.calls == [(["Mail.Read"], True)]
    assert "server-only-token" not in repr(identity())


def test_acquire_token_requires_current_identity() -> None:
    extension = MicrosoftEntraAuth()
    app = create_app()
    extension.init_app(app)

    with app.test_request_context("/"), pytest.raises(AuthenticationRequired):
        extension.acquire_token()


def test_acquire_token_rejects_extension_instance_not_bound_to_current_app() -> None:
    app = create_app()
    registered = MicrosoftEntraAuth()
    other = MicrosoftEntraAuth()
    registered.init_app(app)

    with app.test_request_context("/"):
        bind_identity(identity())
        with pytest.raises(RuntimeError, match="not initialized"):
            other.acquire_token()
