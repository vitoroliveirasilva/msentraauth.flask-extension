from __future__ import annotations

from flask import current_app, g, has_request_context
from werkzeug.local import LocalProxy

from .errors import AuthenticationRequired
from .identity import Identity

_EXTENSION_KEY = "ms_entra_auth"
_IDENTITY_ATTRIBUTE = "_flask_ms_entra_auth_identity"


def bind_identity(identity: Identity) -> None:
    # Identidade validada associada à requisição ativa do Flask
    _require_initialized_request()
    if not isinstance(identity, Identity):
        msg = "identity must be an instance of Identity"
        raise TypeError(msg)
    setattr(g, _IDENTITY_ATTRIBUTE, identity)


def clear_identity() -> None:
    # Remove request-local identity quando presente
    _require_initialized_request()
    g.pop(_IDENTITY_ATTRIBUTE, None)


def get_current_identity() -> Identity:
    # Retorna a identidade vinculada à solicitação ativa ou levanta AuthenticationRequired se nenhuma identidade estiver presente. O estado da identidade é armazenado no objeto de contexto de solicitação do Flask (``flask.g``) e não é persistido na sessão do cliente Flask
    _require_initialized_request()
    identity = g.get(_IDENTITY_ATTRIBUTE)
    if not isinstance(identity, Identity):
        raise AuthenticationRequired("authentication is required")
    return identity


def _require_initialized_request() -> None:
    if not has_request_context():
        raise RuntimeError("current_identity requires an active Flask request context")
    if _EXTENSION_KEY not in current_app.extensions:
        raise RuntimeError("MicrosoftEntraAuth is not initialized for the current application")


current_identity: LocalProxy[Identity] = LocalProxy(get_current_identity)
