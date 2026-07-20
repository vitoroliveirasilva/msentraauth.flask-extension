from ._version import __version__
from .context import current_identity
from .errors import (
    AuthenticationCancelled,
    AuthenticationError,
    AuthenticationRejected,
    AuthenticationRequired,
    ConfigurationError,
    ConsentRequired,
    HookExecutionError,
    IdentityValidationError,
    InvalidCallbackError,
    InvalidNavigationTarget,
    LocalBindingError,
    MicrosoftEntraAuthError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from .extension import MicrosoftEntraAuth
from .hooks import AuthEvent
from .identity import Identity
from .security import SecurityFinding, SecurityReport
from .storage import AtomicAuthStorage, AuthStorage, MemoryStorage
from .web import LoginResult

__all__ = [
    "AtomicAuthStorage",
    "AuthEvent",
    "AuthStorage",
    "AuthenticationCancelled",
    "AuthenticationError",
    "AuthenticationRejected",
    "AuthenticationRequired",
    "ConfigurationError",
    "ConsentRequired",
    "HookExecutionError",
    "Identity",
    "IdentityValidationError",
    "InvalidCallbackError",
    "InvalidNavigationTarget",
    "LocalBindingError",
    "LoginResult",
    "MemoryStorage",
    "MicrosoftEntraAuth",
    "MicrosoftEntraAuthError",
    "ProviderUnavailableError",
    "SecurityFinding",
    "SecurityReport",
    "StorageError",
    "TokenAcquisitionError",
    "__version__",
    "current_identity",
]
