from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from flask import Flask

from .config import ConfigOverrides, MicrosoftEntraAuthConfig, resolve_config
from .storage import AuthStorage, MemoryStorage
from .storage.namespaced import NamespacedStorage

_EXTENSION_KEY = "ms_entra_auth"


@dataclass(slots=True)
class _MicrosoftEntraAuthState:
    # Estado imutável e isolado de uma aplicação Flask, registrado sob ``app.extensions['ms_entra_auth']``

    extension: MicrosoftEntraAuth
    config: MicrosoftEntraAuthConfig
    storage: AuthStorage
    data: dict[str, object] = field(default_factory=dict)


class MicrosoftEntraAuth:
    __slots__ = ("_overrides", "_storage_backend")

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
        session_namespace: str | None = None,
        storage: AuthStorage | None = None,
    ) -> None:
        # Cria a extensão e opcionalmente inicializa uma aplicação Flask
        if storage is not None and not isinstance(storage, AuthStorage):
            msg = "storage must implement AuthStorage"
            raise TypeError(msg)

        self._overrides = ConfigOverrides(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
            authority=authority,
            scopes=(scopes if scopes is None or isinstance(scopes, str) else tuple(scopes)),
            session_namespace=session_namespace,
        )
        self._storage_backend = storage
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        # Valida a configuração e registra o estado isolado da aplicação
        if not isinstance(app, Flask):
            msg = "app must be an instance of flask.Flask"
            raise TypeError(msg)

        if _EXTENSION_KEY in app.extensions:
            state = app.extensions[_EXTENSION_KEY]
            if isinstance(state, _MicrosoftEntraAuthState) and state.extension is self:
                return

            msg = "app.extensions['ms_entra_auth'] is already registered"
            raise RuntimeError(msg)

        config = resolve_config(app.config, self._overrides, app_name=app.import_name)
        backend = self._storage_backend if self._storage_backend is not None else MemoryStorage()
        storage = NamespacedStorage(backend, config.session_namespace)
        app.extensions[_EXTENSION_KEY] = _MicrosoftEntraAuthState(
            extension=self,
            config=config,
            storage=storage,
        )
