from importlib.metadata import version

import flask_ms_entra_auth
from flask_ms_entra_auth import (
    AuthStorage,
    ConfigurationError,
    MemoryStorage,
    MicrosoftEntraAuth,
    MicrosoftEntraAuthError,
    StorageError,
    __version__,
)


def test_package_can_be_imported() -> None:
    assert flask_ms_entra_auth is not None


def test_public_symbols_are_exported() -> None:
    assert flask_ms_entra_auth.AuthStorage is AuthStorage
    assert flask_ms_entra_auth.MemoryStorage is MemoryStorage
    assert flask_ms_entra_auth.MicrosoftEntraAuth is MicrosoftEntraAuth
    assert flask_ms_entra_auth.ConfigurationError is ConfigurationError
    assert flask_ms_entra_auth.MicrosoftEntraAuthError is MicrosoftEntraAuthError
    assert flask_ms_entra_auth.StorageError is StorageError
    assert set(flask_ms_entra_auth.__all__) == {
        "AuthStorage",
        "ConfigurationError",
        "MemoryStorage",
        "MicrosoftEntraAuth",
        "MicrosoftEntraAuthError",
        "StorageError",
        "__version__",
    }


def test_public_errors_inherit_from_public_base_error() -> None:
    assert issubclass(ConfigurationError, MicrosoftEntraAuthError)
    assert issubclass(StorageError, MicrosoftEntraAuthError)


def test_package_version_is_available_from_one_source() -> None:
    assert version("flask-ms-entra-auth") == __version__
