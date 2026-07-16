from importlib.metadata import version

import flask_ms_entra_auth
from flask_ms_entra_auth import MicrosoftEntraAuth, __version__


def test_package_can_be_imported() -> None:
    assert flask_ms_entra_auth is not None


def test_microsoft_entra_auth_is_publicly_exported() -> None:
    assert flask_ms_entra_auth.MicrosoftEntraAuth is MicrosoftEntraAuth
    assert "MicrosoftEntraAuth" in flask_ms_entra_auth.__all__


def test_package_version_is_available_from_one_source() -> None:
    assert __version__ == "0.1.0"
    assert version("flask-ms-entra-auth") == __version__
