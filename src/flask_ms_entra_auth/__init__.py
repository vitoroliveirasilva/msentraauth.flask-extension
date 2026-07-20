from ._version import __version__
from .context import current_identity
from .errors import (
    AuthenticationCancelled,
    AuthenticationError,
    AuthenticationRequired,
    ConfigurationError,
    ConsentRequired,
    IdentityValidationError,
    InvalidCallbackError,
    InvalidNavigationTarget,
    MicrosoftEntraAuthError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from .extension import MicrosoftEntraAuth
from .identity import Identity
from .storage import AuthStorage, MemoryStorage
from .web import LoginResult

__all__ = [
    "AuthStorage",
    "AuthenticationCancelled",
    "AuthenticationError",
    "AuthenticationRequired",
    "ConfigurationError",
    "ConsentRequired",
    "Identity",
    "IdentityValidationError",
    "InvalidCallbackError",
    "InvalidNavigationTarget",
    "LoginResult",
    "MemoryStorage",
    "MicrosoftEntraAuth",
    "MicrosoftEntraAuthError",
    "ProviderUnavailableError",
    "StorageError",
    "TokenAcquisitionError",
    "__version__",
    "current_identity",
]
