from __future__ import annotations

from typing import Any

import pytest
from flask import Flask

from flask_ms_entra_auth import (
    AuthenticationRequired,
    Identity,
    MicrosoftEntraAuth,
    current_identity,
)
from flask_ms_entra_auth.context import (
    bind_identity,
    clear_identity,
    get_current_identity,
)

_VALID_CONFIG = {
    "MS_ENTRA_CLIENT_ID": "client-id",
    "MS_ENTRA_CLIENT_SECRET": "unit-test-secret",
    "MS_ENTRA_TENANT_ID": "tenant-id",
    "MS_ENTRA_REDIRECT_URI": "http://localhost/auth/callback",
}


def create_app(name: str = "context") -> Flask:
    app = Flask(name)
    app.config.from_mapping(_VALID_CONFIG)
    return app


def identity(object_id: str = "object-id") -> Identity:
    return Identity(
        object_id=object_id,
        tenant_id="tenant-id",
        home_account_id=f"home-{object_id}",
    )


def test_current_identity_outside_request_context_fails_explicitly() -> None:
    with pytest.raises(RuntimeError, match="active Flask request context"):
        get_current_identity()


def test_current_identity_requires_initialized_extension() -> None:
    app = create_app()

    with (
        app.test_request_context("/"),
        pytest.raises(RuntimeError, match="not initialized"),
    ):
        get_current_identity()


def test_current_identity_requires_authentication() -> None:
    app = create_app()
    MicrosoftEntraAuth().init_app(app)

    with (
        app.test_request_context("/"),
        pytest.raises(AuthenticationRequired, match="authentication is required"),
    ):
        get_current_identity()


def test_bind_identity_populates_function_and_local_proxy() -> None:
    app = create_app()
    MicrosoftEntraAuth().init_app(app)
    expected = identity()

    with app.test_request_context("/"):
        bind_identity(expected)

        assert get_current_identity() is expected
        assert current_identity.object_id == "object-id"  # type: ignore[attr-defined]
        assert current_identity._get_current_object() is expected


def test_clear_identity_is_idempotent_and_restores_authentication_required() -> None:
    app = create_app()
    MicrosoftEntraAuth().init_app(app)

    with app.test_request_context("/"):
        bind_identity(identity())
        clear_identity()
        clear_identity()

        with pytest.raises(AuthenticationRequired):
            get_current_identity()


def test_bind_identity_rejects_invalid_object() -> None:
    app = create_app()
    MicrosoftEntraAuth().init_app(app)
    invalid_identity: Any = object()

    with app.test_request_context("/"), pytest.raises(TypeError, match="Identity"):
        bind_identity(invalid_identity)


def test_identity_is_isolated_between_requests() -> None:
    app = create_app()
    MicrosoftEntraAuth().init_app(app)

    with app.test_request_context("/first"):
        bind_identity(identity("first"))
        assert current_identity.object_id == "first"  # type: ignore[attr-defined]

    with app.test_request_context("/second"), pytest.raises(AuthenticationRequired):
        get_current_identity()


def test_identity_is_isolated_between_apps() -> None:
    first = create_app("first")
    second = create_app("second")
    extension = MicrosoftEntraAuth()
    extension.init_app(first)
    extension.init_app(second)

    with first.test_request_context("/"):
        bind_identity(identity("first"))
        assert current_identity.object_id == "first"  # type: ignore[attr-defined]

    with second.test_request_context("/"), pytest.raises(AuthenticationRequired):
        get_current_identity()
