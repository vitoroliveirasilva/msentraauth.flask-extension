from typing import Any

import pytest
from flask import Flask

from flask_ms_entra_auth import MicrosoftEntraAuth


def create_app(name: str) -> Flask:
    return Flask(name)


def test_init_app_registers_extension_state() -> None:
    app = create_app("registered")
    extension = MicrosoftEntraAuth()

    extension.init_app(app)

    state = app.extensions["ms_entra_auth"]
    assert state.extension is extension
    assert state.data == {}


def test_same_instance_initializes_two_distinct_apps() -> None:
    extension = MicrosoftEntraAuth()
    first_app = create_app("first")
    second_app = create_app("second")

    extension.init_app(first_app)
    extension.init_app(second_app)

    assert first_app.extensions["ms_entra_auth"].extension is extension
    assert second_app.extensions["ms_entra_auth"].extension is extension
    assert first_app.extensions["ms_entra_auth"] is not second_app.extensions["ms_entra_auth"]


def test_extension_does_not_store_app_on_self() -> None:
    extension = MicrosoftEntraAuth(create_app("constructor"))

    assert not hasattr(extension, "app")


def test_apps_do_not_share_mutable_state() -> None:
    extension = MicrosoftEntraAuth()
    first_app = create_app("mutable-first")
    second_app = create_app("mutable-second")
    extension.init_app(first_app)
    extension.init_app(second_app)

    first_state = first_app.extensions["ms_entra_auth"]
    second_state = second_app.extensions["ms_entra_auth"]
    first_state.data["marker"] = object()

    assert "marker" not in second_state.data


def test_duplicate_initialization_with_same_instance_is_idempotent() -> None:
    app = create_app("idempotent")
    extension = MicrosoftEntraAuth()
    extension.init_app(app)
    original_state = app.extensions["ms_entra_auth"]

    extension.init_app(app)

    assert app.extensions["ms_entra_auth"] is original_state


def test_duplicate_initialization_with_other_instance_is_rejected() -> None:
    app = create_app("conflict")
    first_extension = MicrosoftEntraAuth()
    second_extension = MicrosoftEntraAuth()
    first_extension.init_app(app)

    with pytest.raises(RuntimeError, match="already registered"):
        second_extension.init_app(app)

    assert app.extensions["ms_entra_auth"].extension is first_extension


def test_invalid_app_argument_is_rejected() -> None:
    extension = MicrosoftEntraAuth()
    invalid_app: Any = object()

    with pytest.raises(TypeError, match=r"flask\.Flask"):
        extension.init_app(invalid_app)


def test_init_app_does_not_register_routes() -> None:
    app = create_app("routes")
    extension = MicrosoftEntraAuth()
    rules_before = tuple(app.url_map.iter_rules())

    extension.init_app(app)

    assert tuple(app.url_map.iter_rules()) == rules_before
