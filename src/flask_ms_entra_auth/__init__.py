from ._version import __version__
from .errors import ConfigurationError, MicrosoftEntraAuthError
from .extension import MicrosoftEntraAuth

__all__ = [
    "ConfigurationError",
    "MicrosoftEntraAuth",
    "MicrosoftEntraAuthError",
    "__version__",
]
