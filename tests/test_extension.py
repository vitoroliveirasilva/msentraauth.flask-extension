from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from flask import Flask

from flask_ms_entra_auth import AuthStorage, MemoryStorage, MicrosoftEntraAuth
from flask_ms_entra_auth.storage.namespaced import NamespacedStorage

_VALID_CONFIG: dict[str, object] = {
    "MS_ENTRA_CLIENT_ID": "11111111-1111-1111-1111-111111111111",
    "MS_ENTRA_CLIENT_SECRET": "unit-test-secret",
    "MS_ENTRA_TENANT_ID": "22222222-2222-2222-2222-222222222222",
    "MS_ENTRA_REDIRECT_URI": "http://localhost/auth/callback",
}


def create_app(name: str, **overrides: object) -> Flask:
    app = Flask(name)
    app.config.from_mapping(_VALID_CONFIG)
    app.config.update(overrides)
    return app


def test_init_app_registers_extension_and_resolved_config() -> None:
    app = create_app("registered")
    extension = MicrosoftEntraAuth()

    extension.init_app(app)

    state = app.extensions["ms_entra_auth"]
    assert state.extension is extension
    assert state.data == {}
    assert state.config.client_id == _VALID_CONFIG["MS_ENTRA_CLIENT_ID"]
    assert state.config.client_secret == _VALID_CONFIG["MS_ENTRA_CLIENT_SECRET"]
    assert state.config.authority == (
        "https://login.microsoftonline.com/22222222-2222-2222-2222-222222222222"
    )
    assert state.config.scopes == ("User.Read",)
    assert "unit-test-secret" not in repr(state.config)


def test_same_instance_initializes_two_apps_with_isolated_configuration() -> None:
    extension = MicrosoftEntraAuth()
    first_app = create_app("first", MS_ENTRA_CLIENT_ID="first-client")
    second_app = create_app("second", MS_ENTRA_CLIENT_ID="second-client")

    extension.init_app(first_app)
    extension.init_app(second_app)

    first_state = first_app.extensions["ms_entra_auth"]
    second_state = second_app.extensions["ms_entra_auth"]
    assert first_state.extension is extension
    assert second_state.extension is extension
    assert first_state is not second_state
    assert first_state.config is not second_state.config
    assert first_state.config.client_id == "first-client"
    assert second_state.config.client_id == "second-client"


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


def test_duplicate_initialization_is_idempotent_and_freezes_original_config() -> None:
    app = create_app("idempotent")
    extension = MicrosoftEntraAuth()
    extension.init_app(app)
    original_state = app.extensions["ms_entra_auth"]
    original_client_id = original_state.config.client_id
    app.config["MS_ENTRA_CLIENT_ID"] = "changed-after-initialization"

    extension.init_app(app)

    assert app.extensions["ms_entra_auth"] is original_state
    assert original_state.config.client_id == original_client_id


def test_duplicate_initialization_with_other_instance_is_rejected() -> None:
    app = create_app("conflict")
    first_extension = MicrosoftEntraAuth()
    second_extension = MicrosoftEntraAuth()
    first_extension.init_app(app)

    with pytest.raises(RuntimeError, match="already registered"):
        second_extension.init_app(app)

    assert app.extensions["ms_entra_auth"].extension is first_extension


def test_incompatible_existing_extension_state_is_rejected() -> None:
    app = create_app("incompatible")
    app.extensions["ms_entra_auth"] = object()

    with pytest.raises(RuntimeError, match="already registered"):
        MicrosoftEntraAuth().init_app(app)


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


def test_constructor_arguments_override_flask_configuration() -> None:
    app = create_app(
        "precedence",
        MS_ENTRA_CLIENT_ID="app-client",
        MS_ENTRA_CLIENT_SECRET="app-secret",
        MS_ENTRA_TENANT_ID="app.example.com",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/callback",
        MS_ENTRA_AUTHORITY="https://login.example.com/app.example.com",
        MS_ENTRA_SCOPES=["App.Scope"],
    )
    extension = MicrosoftEntraAuth(
        client_id="constructor-client",
        client_secret="constructor-secret",
        tenant_id="constructor.example.com",
        redirect_uri="https://constructor.example.com/callback",
        authority="https://login.example.com/constructor.example.com/",
        scopes=["Constructor.Scope", "Constructor.Scope", "Another.Scope"],
    )

    extension.init_app(app)

    config = app.extensions["ms_entra_auth"].config
    assert config.client_id == "constructor-client"
    assert config.client_secret == "constructor-secret"
    assert config.tenant_id == "constructor.example.com"
    assert config.redirect_uri == "https://constructor.example.com/callback"
    assert config.authority == "https://login.example.com/constructor.example.com"
    assert config.scopes == ("Constructor.Scope", "Another.Scope")


def test_constructor_copies_mutable_scopes() -> None:
    scopes = ["Scope.Read"]
    extension = MicrosoftEntraAuth(scopes=scopes)
    scopes.append("Scope.Write")
    app = create_app("copied-scopes")

    extension.init_app(app)

    assert app.extensions["ms_entra_auth"].config.scopes == ("Scope.Read",)


def test_resolved_configuration_is_immutable() -> None:
    app = create_app("immutable")
    MicrosoftEntraAuth().init_app(app)
    config = app.extensions["ms_entra_auth"].config

    with pytest.raises(FrozenInstanceError):
        config.client_id = "changed"


def test_init_app_registers_namespaced_storage() -> None:
    app = create_app("storage-state", MS_ENTRA_SESSION_NAMESPACE="storage-state")

    MicrosoftEntraAuth().init_app(app)

    state = app.extensions["ms_entra_auth"]
    assert isinstance(state.storage, AuthStorage)
    assert isinstance(state.storage, NamespacedStorage)
    assert state.storage.namespace == "storage-state"
    state.storage.save("flow", b"value")
    assert state.storage.load("flow") == b"value"


def test_default_memory_storage_is_not_shared_between_apps() -> None:
    extension = MicrosoftEntraAuth()
    first_app = create_app("same-name")
    second_app = create_app("same-name")
    extension.init_app(first_app)
    extension.init_app(second_app)

    first_storage = first_app.extensions["ms_entra_auth"].storage
    second_storage = second_app.extensions["ms_entra_auth"].storage
    first_storage.save("cache", b"first")

    assert second_storage.load("cache") is None


def test_shared_backend_is_isolated_by_application_namespace() -> None:
    backend = MemoryStorage()
    extension = MicrosoftEntraAuth(storage=backend)
    first_app = create_app("shared-first")
    second_app = create_app("shared-second")
    extension.init_app(first_app)
    extension.init_app(second_app)

    first_state = first_app.extensions["ms_entra_auth"]
    second_state = second_app.extensions["ms_entra_auth"]
    first_state.storage.save("cache", b"first")
    second_state.storage.save("cache", b"second")

    assert first_state.config.session_namespace != second_state.config.session_namespace
    assert first_state.storage.load("cache") == b"first"
    assert second_state.storage.load("cache") == b"second"


def test_constructor_storage_namespace_overrides_app_configuration() -> None:
    app = create_app("namespace-precedence", MS_ENTRA_SESSION_NAMESPACE="from-app")
    extension = MicrosoftEntraAuth(session_namespace="from-constructor")

    extension.init_app(app)

    state = app.extensions["ms_entra_auth"]
    assert state.config.session_namespace == "from-constructor"
    assert state.storage.namespace == "from-constructor"


def test_duplicate_initialization_preserves_storage_instance() -> None:
    app = create_app("storage-idempotent")
    extension = MicrosoftEntraAuth()
    extension.init_app(app)
    original_storage = app.extensions["ms_entra_auth"].storage

    extension.init_app(app)

    assert app.extensions["ms_entra_auth"].storage is original_storage


def test_constructor_rejects_invalid_storage_backend() -> None:
    invalid_storage: Any = object()

    with pytest.raises(TypeError, match="AuthStorage"):
        MicrosoftEntraAuth(storage=invalid_storage)
