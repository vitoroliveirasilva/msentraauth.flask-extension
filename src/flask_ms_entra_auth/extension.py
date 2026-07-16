from __future__ import annotations

from dataclasses import dataclass, field

from flask import Flask

_EXTENSION_KEY = "ms_entra_auth"


@dataclass(slots=True)
class _MicrosoftEntraAuthState:
    # Estado da extensão Microsoft Entra Auth para um aplicativo Flask específico

    extension: MicrosoftEntraAuth
    data: dict[str, object] = field(default_factory=dict)


class MicrosoftEntraAuth:
    # Fundação para a extensão de autenticação Microsoft Entra do Flask

    __slots__ = ()

    def __init__(self, app: Flask | None = None) -> None:
        # Cria a instância da extensão e se fornecido, inicializa o aplicativo Flask
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        # Registra o estado da extensão Microsoft Entra Auth no aplicativo Flask fornecido
        if not isinstance(app, Flask):
            msg = "app must be an instance of flask.Flask"
            raise TypeError(msg)

        if _EXTENSION_KEY in app.extensions:
            state = app.extensions[_EXTENSION_KEY]
            if isinstance(state, _MicrosoftEntraAuthState) and state.extension is self:
                return

            msg = "app.extensions['ms_entra_auth'] is already registered"
            raise RuntimeError(msg)

        app.extensions[_EXTENSION_KEY] = _MicrosoftEntraAuthState(extension=self)
