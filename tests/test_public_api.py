from importlib.metadata import version

import flask_ms_entra_auth
from flask_ms_entra_auth import (
    AtomicAuthStorage,
    AuthenticationCancelled,
    AuthenticationError,
    AuthenticationRejected,
    AuthenticationRequired,
    AuthEvent,
    AuthStorage,
    ConfigurationError,
    ConsentRequired,
    HookExecutionError,
    Identity,
    IdentityValidationError,
    InvalidCallbackError,
    InvalidNavigationTarget,
    LocalBindingError,
    LoginResult,
    MemoryStorage,
    MicrosoftEntraAuth,
    MicrosoftEntraAuthError,
    ProviderUnavailableError,
    SecurityFinding,
    SecurityReport,
    StorageError,
    TokenAcquisitionError,
    __version__,
    current_identity,
)


def test_package_can_be_imported() -> None:
    assert flask_ms_entra_auth is not None


def test_public_symbols_are_exported() -> None:
    expected = {
        "AtomicAuthStorage": AtomicAuthStorage,
        "AuthEvent": AuthEvent,
        "AuthStorage": AuthStorage,
        "AuthenticationCancelled": AuthenticationCancelled,
        "AuthenticationError": AuthenticationError,
        "AuthenticationRejected": AuthenticationRejected,
        "AuthenticationRequired": AuthenticationRequired,
        "ConfigurationError": ConfigurationError,
        "ConsentRequired": ConsentRequired,
        "HookExecutionError": HookExecutionError,
        "Identity": Identity,
        "IdentityValidationError": IdentityValidationError,
        "InvalidCallbackError": InvalidCallbackError,
        "InvalidNavigationTarget": InvalidNavigationTarget,
        "LocalBindingError": LocalBindingError,
        "LoginResult": LoginResult,
        "MemoryStorage": MemoryStorage,
        "MicrosoftEntraAuth": MicrosoftEntraAuth,
        "MicrosoftEntraAuthError": MicrosoftEntraAuthError,
        "ProviderUnavailableError": ProviderUnavailableError,
        "SecurityFinding": SecurityFinding,
        "SecurityReport": SecurityReport,
        "StorageError": StorageError,
        "TokenAcquisitionError": TokenAcquisitionError,
        "current_identity": current_identity,
    }

    for name, value in expected.items():
        assert getattr(flask_ms_entra_auth, name) is value
    assert set(flask_ms_entra_auth.__all__) == {*expected, "__version__"}


def test_public_errors_inherit_from_public_base_error() -> None:
    for error in (
        AuthenticationError,
        AuthenticationRejected,
        ConfigurationError,
        ProviderUnavailableError,
        StorageError,
        TokenAcquisitionError,
        HookExecutionError,
        LocalBindingError,
    ):
        assert issubclass(error, MicrosoftEntraAuthError)
    for error in (
        AuthenticationCancelled,
        AuthenticationRejected,
        AuthenticationRequired,
        ConsentRequired,
        IdentityValidationError,
        InvalidCallbackError,
        InvalidNavigationTarget,
    ):
        assert issubclass(error, AuthenticationError)


def test_token_acquisition_error_exposes_only_sanitized_metadata_fields() -> None:
    error = TokenAcquisitionError(
        "safe message",
        code="invalid_grant",
        correlation_id="abc-123",
    )

    assert str(error) == "safe message"
    assert error.code == "invalid_grant"
    assert error.correlation_id == "abc-123"


def test_package_version_is_available_from_one_source() -> None:
    assert version("flask-ms-entra-auth") == __version__
