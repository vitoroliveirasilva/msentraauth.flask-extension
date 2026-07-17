from ._version import __version__
from .errors import ConfigurationError, MicrosoftEntraAuthError, StorageError
from .extension import MicrosoftEntraAuth
from .storage import AuthStorage, MemoryStorage

__all__ = [
    "AuthStorage",
    "ConfigurationError",
    "MemoryStorage",
    "MicrosoftEntraAuth",
    "MicrosoftEntraAuthError",
    "StorageError",
    "__version__",
]
