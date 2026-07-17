from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from flask import Flask, current_app

from .auth import MsalService
from .auth.client import create_confidential_client
from .auth.protocols import MsalClientFactory
from .config import ConfigOverrides, MicrosoftEntraAuthConfig, resolve_config
from .context import get_current_identity
from .storage import AuthStorage, MemoryStorage
from .storage.namespaced import NamespacedStorage

_EXTENSION_KEY = "ms_entra_auth"


@dataclass(slots=True)
class _MicrosoftEntraAuthState:
    """State owned by exactly one Flask application."""

    extension: MicrosoftEntraAuth
    config: MicrosoftEntraAuthConfig
    storage: AuthStorage
    msal: MsalService
    data: dict[str, object] = field(default_factory=dict)


class MicrosoftEntraAuth:
    # A instância armazena substituições de construtor imutáveis e fábricas de backend injetáveis, mas nunca armazena uma aplicação Flask. O estado da aplicação resolvido vive sob ``app.extensions['ms_entra_auth']``

    __slots__ = ("_client_factory", "_overrides", "_storage_backend")

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
        token_cache_ttl: int | None = None,
        storage: AuthStorage | None = None,
        msal_client_factory: MsalClientFactory | None = None,
    ) -> None:
        # Cria a extensão e opcionalmente inicializa uma aplicação Flask
        if storage is not None and not isinstance(storage, AuthStorage):
            msg = "storage must implement AuthStorage"
            raise TypeError(msg)
        if msal_client_factory is not None and not callable(msal_client_factory):
            msg = "msal_client_factory must be callable"
            raise TypeError(msg)

        self._overrides = ConfigOverrides(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
            authority=authority,
            scopes=(scopes if scopes is None or isinstance(scopes, str) else tuple(scopes)),
            session_namespace=session_namespace,
            token_cache_ttl=token_cache_ttl,
        )
        self._storage_backend = storage
        self._client_factory = msal_client_factory or create_confidential_client
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        # Valida a configuração e registra o estado da aplicação isolada. A repetição da inicialização com esta mesma instância de extensão é uma operação sem efeito idempotente e preserva a configuração, armazenamento e serviço MSAL resolvidos originais. A inicialização com outra instância para uma chave de extensão ocupada gera ``RuntimeError``
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
        msal_service = MsalService(
            config=config,
            storage=storage,
            client_factory=self._client_factory,
        )
        app.extensions[_EXTENSION_KEY] = _MicrosoftEntraAuthState(
            extension=self,
            config=config,
            storage=storage,
            msal=msal_service,
        )

    def acquire_token(
        self,
        scopes: Iterable[str] | None = None,
        *,
        force_refresh: bool = False,
    ) -> str:
        # Adquire um token de acesso delegado silenciosamente para a identidade atual. O token é retornado apenas para o código do aplicativo do lado do servidor e nunca é adicionado ao objeto de identidade ou à sessão do cliente Flask
        identity = get_current_identity()
        state = self._current_state()
        return state.msal.acquire_token_silent(
            home_account_id=identity.home_account_id,
            scopes=scopes,
            force_refresh=force_refresh,
        )

    def _current_state(self) -> _MicrosoftEntraAuthState:
        state = current_app.extensions.get(_EXTENSION_KEY)
        if not isinstance(state, _MicrosoftEntraAuthState) or state.extension is not self:
            raise RuntimeError("MicrosoftEntraAuth is not initialized for the current application")
        return state
