from ._version import __version__
from .context import current_identity
from .errors import (
    AuthenticationError,
    AuthenticationRequired,
    ConfigurationError,
    ConsentRequired,
    IdentityValidationError,
    MicrosoftEntraAuthError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from .extension import MicrosoftEntraAuth
from .identity import Identity
from .storage import AuthStorage, MemoryStorage

__all__ = [
    "AuthStorage",
    "AuthenticationError",
    "AuthenticationRequired",
    "ConfigurationError",
    "ConsentRequired",
    "Identity",
    "IdentityValidationError",
    "MemoryStorage",
    "MicrosoftEntraAuth",
    "MicrosoftEntraAuthError",
    "ProviderUnavailableError",
    "StorageError",
    "TokenAcquisitionError",
    "__version__",
    "current_identity",
]
