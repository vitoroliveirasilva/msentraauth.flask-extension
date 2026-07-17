from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from flask import Flask

from .config import ConfigOverrides, MicrosoftEntraAuthConfig, resolve_config

_EXTENSION_KEY = "ms_entra_auth"


@dataclass(slots=True)
class _MicrosoftEntraAuthState:
    # Estado da extensão Microsoft Entra Auth para um aplicativo Flask específico

    extension: MicrosoftEntraAuth
    config: MicrosoftEntraAuthConfig
    data: dict[str, object] = field(default_factory=dict)


class MicrosoftEntraAuth:
    # Fundação para a extensão de autenticação Microsoft Entra do Flask

    __slots__ = ("_overrides",)

    def __init__(
        self,
        app: Flask | None = None,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        tenant_id: str | None = None,
        redirect_uri: str | None = None,
        authority: str | None = None,
        scopes: Iterable[str] | None = None,
    ) -> None:
        # Cria a instância da extensão e se fornecido, inicializa o aplicativo Flask
        self._overrides = ConfigOverrides(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
            authority=authority,
            scopes=(scopes if scopes is None or isinstance(scopes, str) else tuple(scopes)),
        )
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

        config = resolve_config(app.config, self._overrides)
        app.extensions[_EXTENSION_KEY] = _MicrosoftEntraAuthState(
            extension=self,
            config=config,
        )
