from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from functools import wraps
from time import perf_counter
from typing import ParamSpec, overload

from flask import Flask, current_app, redirect, request, url_for
from flask.typing import ResponseReturnValue

from .auth import MsalService
from .auth.client import create_confidential_client
from .auth.flow import AuthCodeFlowService
from .auth.protocols import MsalClientFactory
from .auth.token_cache import delete_token_cache
from .config import ConfigOverrides, MicrosoftEntraAuthConfig, resolve_config
from .context import get_current_identity
from .errors import (
    AuthenticationRequired,
    ConfigurationError,
    MicrosoftEntraAuthError,
    StorageError,
)
from .hooks import (
    AuthenticatedHook,
    AuthEvent,
    ErrorHook,
    EventHook,
    HookRegistry,
    LogoutHook,
)
from .observability import Observability
from .security import SecurityReport
from .security import audit_security as _audit_security
from .storage import AuthStorage, MemoryStorage
from .storage.namespaced import NamespacedStorage
from .web.models import LoginResult
from .web.routes import _safe_error_response, blueprint_name, create_auth_blueprint
from .web.session import WebSessionManager
from .web.urls import validate_next_url

_EXTENSION_KEY = "ms_entra_auth"
_LOGGER_NAME = "flask_ms_entra_auth"
_P = ParamSpec("_P")


@dataclass(slots=True)
class _MicrosoftEntraAuthState:
    # Estado do MicrosoftEntraAuth para uma aplicação Flask específica. Contém a configuração, armazenamento, serviços MSAL e fluxo de autenticação, gerenciador de sessão web e informações sobre o registro de rotas.

    extension: MicrosoftEntraAuth
    config: MicrosoftEntraAuthConfig
    storage: NamespacedStorage
    msal: MsalService
    flow: AuthCodeFlowService
    web_session: WebSessionManager
    observability: Observability
    security_report: SecurityReport
    routes_registered: bool = False
    data: dict[str, object] = field(default_factory=dict)


class MicrosoftEntraAuth:
    # MS Entra Autenticação para aplicações Flask. A instância armazena substituições de construtor imutáveis e fábricas de back-end injetáveis, mas nunca armazena uma aplicação Flask. O estado da aplicação resolvido vive sob ``app.extensions['ms_entra_auth']``.

    __slots__ = ("_client_factory", "_hooks", "_overrides", "_storage_backend")

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
        flow_ttl: int | None = None,
        identity_ttl: int | None = None,
        url_prefix: str | None = None,
        post_login_redirect_uri: str | None = None,
        post_logout_redirect_uri: str | None = None,
        allowed_next_hosts: Iterable[str] | None = None,
        auto_register_routes: bool | None = None,
        handle_route_errors: bool | None = None,
        unauthenticated_mode: str | None = None,
        event_logging: bool | None = None,
        request_id_header: str | None = None,
        require_atomic_storage: bool | None = None,
        strict_security: bool | None = None,
        storage: AuthStorage | None = None,
        msal_client_factory: MsalClientFactory | None = None,
    ) -> None:
        # Cria a extensão e opcionalmente inicializa uma aplicação Flask
        if storage is not None and not isinstance(storage, AuthStorage):
            raise TypeError("storage must implement AuthStorage")
        if msal_client_factory is not None and not callable(msal_client_factory):
            raise TypeError("msal_client_factory must be callable")

        self._overrides = ConfigOverrides(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
            authority=authority,
            scopes=(scopes if scopes is None or isinstance(scopes, str) else tuple(scopes)),
            session_namespace=session_namespace,
            token_cache_ttl=token_cache_ttl,
            flow_ttl=flow_ttl,
            identity_ttl=identity_ttl,
            url_prefix=url_prefix,
            post_login_redirect_uri=post_login_redirect_uri,
            post_logout_redirect_uri=post_logout_redirect_uri,
            allowed_next_hosts=(
                allowed_next_hosts
                if allowed_next_hosts is None or isinstance(allowed_next_hosts, str)
                else tuple(allowed_next_hosts)
            ),
            auto_register_routes=auto_register_routes,
            handle_route_errors=handle_route_errors,
            unauthenticated_mode=unauthenticated_mode,
            event_logging=event_logging,
            request_id_header=request_id_header,
            require_atomic_storage=require_atomic_storage,
            strict_security=strict_security,
        )
        self._storage_backend = storage
        self._client_factory = msal_client_factory or create_confidential_client
        self._hooks = HookRegistry()
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        # Valida a configuração e registra o estado da aplicação isolada. Repetir a inicialização com esta mesma instância de extensão é uma operação sem efeito idempotente e preserva o estado resolvido original
        if not isinstance(app, Flask):
            raise TypeError("app must be an instance of flask.Flask")

        if _EXTENSION_KEY in app.extensions:
            state = app.extensions[_EXTENSION_KEY]
            if isinstance(state, _MicrosoftEntraAuthState) and state.extension is self:
                return
            raise RuntimeError("app.extensions['ms_entra_auth'] is already registered")

        config = resolve_config(app.config, self._overrides, app_name=app.import_name)
        backend = self._storage_backend if self._storage_backend is not None else MemoryStorage()
        storage = NamespacedStorage(backend, config.session_namespace)
        if config.require_atomic_storage and not storage.supports_atomic_take:
            raise ConfigurationError("configured storage must support atomic one-time consumption")

        security_report = _audit_security(app, config, storage)
        if config.strict_security and not security_report.passed:
            codes = ", ".join(
                finding.code for finding in security_report.findings if finding.severity == "error"
            )
            raise ConfigurationError(f"security audit failed: {codes}")

        observability = Observability(
            config,
            self._hooks,
            logging.getLogger(_LOGGER_NAME),
        )
        msal_service = MsalService(
            config=config,
            storage=storage,
            client_factory=self._client_factory,
        )
        flow_service = AuthCodeFlowService(
            config=config,
            storage=storage,
            client_factory=self._client_factory,
        )
        web_session = WebSessionManager(config, storage)
        state = _MicrosoftEntraAuthState(
            extension=self,
            config=config,
            storage=storage,
            msal=msal_service,
            flow=flow_service,
            web_session=web_session,
            observability=observability,
            security_report=security_report,
        )
        app.extensions[_EXTENSION_KEY] = state

        @app.before_request
        def _restore_ms_entra_identity() -> ResponseReturnValue | None:
            current_state = app.extensions.get(_EXTENSION_KEY)
            if not isinstance(current_state, _MicrosoftEntraAuthState):
                return None
            try:
                identity = current_state.web_session.restore_identity()
            except MicrosoftEntraAuthError as exc:
                current_state.observability.emit_error(exc)
                if current_state.config.handle_route_errors:
                    return _safe_error_response(exc)
                raise
            if identity is not None:
                current_state.observability.emit("identity_restored")
            return None

        if config.auto_register_routes:
            self.register_routes(app)

    def register_routes(self, app: Flask) -> None:
        # Registra o blueprint de login, callback e logout POST opcional. Repetir a chamada com a mesma aplicação é uma operação sem efeito idempotente e preserva o estado original do registro de rotas
        if not isinstance(app, Flask):
            raise TypeError("app must be an instance of flask.Flask")
        state = self._state_for_app(app)
        if state.routes_registered:
            return
        if blueprint_name() in app.blueprints:
            raise RuntimeError("the 'ms_entra_auth' blueprint name is already registered")

        app.register_blueprint(
            create_auth_blueprint(self, state.config),
            url_prefix=state.config.url_prefix,
        )
        state.routes_registered = True

    def begin_login(
        self,
        next_url: str | None = None,
        scopes: Iterable[str] | None = None,
    ) -> str:
        # Inicia um fluxo de login interativo e retorna a URI de autorização do provedor. O fluxo é armazenado na sessão web para que possa ser consumido posteriormente no callback
        state = self._current_state()
        started_at = perf_counter()
        try:
            state.web_session.require_secure_session()
            safe_next_url = validate_next_url(next_url, state.config)

            previous_flow_id = state.web_session.discard_pending_flow()
            if previous_flow_id is not None:
                state.flow.discard(previous_flow_id)

            started = state.flow.begin_login(next_url=safe_next_url, scopes=scopes)
            try:
                state.web_session.set_pending_flow(started.flow_id)
            except Exception:
                state.flow.discard(started.flow_id)
                raise
        except MicrosoftEntraAuthError as exc:
            state.observability.emit_error(exc)
            raise

        state.observability.emit(
            "authentication_started",
            duration_ms=_elapsed_ms(started_at),
        )
        return started.auth_uri

    def complete_login(self, auth_response: Mapping[str, object]) -> LoginResult:
        # Consome um fluxo de login pendente, persiste a identidade resultante e retorna a URL de redirecionamento segura
        state = self._current_state()
        started_at = perf_counter()
        result: LoginResult | None = None
        try:
            flow_id = state.web_session.consume_pending_flow()
            result = state.flow.complete_login(flow_id=flow_id, auth_response=auth_response)
            self._hooks.emit_authenticated(result.identity)
            state.web_session.establish_identity(result.identity)
        except MicrosoftEntraAuthError as exc:
            if result is not None:
                try:
                    delete_token_cache(state.storage, result.identity.home_account_id)
                except StorageError as cleanup_error:
                    state.observability.emit_error(cleanup_error)
            state.observability.emit_error(exc)
            raise

        state.observability.emit(
            "authentication_succeeded",
            duration_ms=_elapsed_ms(started_at),
        )
        return result

    def logout(self) -> str:
        # Limpa apenas a identidade local desta sessão do navegador, o fluxo e o cache de tokens
        state = self._current_state()
        started_at = perf_counter()
        try:
            state.web_session.require_secure_session()

            pending_flow_id = state.web_session.discard_pending_flow()
            if pending_flow_id is not None:
                state.flow.discard(pending_flow_id)

            identity = state.web_session.clear_authentication()
            if identity is not None:
                delete_token_cache(state.storage, identity.home_account_id)
            self._hooks.emit_logout(identity)
        except MicrosoftEntraAuthError as exc:
            state.observability.emit_error(exc)
            raise

        state.observability.emit("logout_completed", duration_ms=_elapsed_ms(started_at))
        return state.config.post_logout_redirect_uri

    def acquire_token(
        self,
        scopes: Iterable[str] | None = None,
        *,
        force_refresh: bool = False,
    ) -> str:
        # Adquire silenciosamente um token de acesso delegado para ``current_identity``
        state = self._current_state()
        started_at = perf_counter()
        try:
            identity = get_current_identity()
            token = state.msal.acquire_token_silent(
                home_account_id=identity.home_account_id,
                scopes=scopes,
                force_refresh=force_refresh,
            )
        except MicrosoftEntraAuthError as exc:
            state.observability.emit_error(exc)
            raise
        state.observability.emit("token_acquired", duration_ms=_elapsed_ms(started_at))
        return token

    def on_authenticated(self, callback: AuthenticatedHook) -> AuthenticatedHook:
        # Registra um hook local executado antes do estabelecimento da sessão
        return self._hooks.on_authenticated(callback)

    def on_logout(self, callback: LogoutHook) -> LogoutHook:
        # Registra um hook executado após a limpeza local do logout
        return self._hooks.on_logout(callback)

    def on_error(self, callback: ErrorHook) -> ErrorHook:
        # Registra um hook para erros previsíveis da extensão
        return self._hooks.on_error(callback)

    def on_event(self, callback: EventHook) -> EventHook:
        # Registra um hook para eventos estruturados sanitizados
        return self._hooks.on_event(callback)

    def audit_security(self, app: Flask | None = None) -> SecurityReport:
        # Retorna um relatório de postura de segurança atualizado e somente leitura
        if app is None:
            state = self._current_state()
            target_app = current_app
        else:
            if not isinstance(app, Flask):
                raise TypeError("app must be an instance of flask.Flask")
            state = self._state_for_app(app)
            target_app = app
        report = _audit_security(target_app, state.config, state.storage)
        state.security_report = report
        return report

    @overload
    def login_required(
        self,
        view: Callable[_P, ResponseReturnValue],
        /,
    ) -> Callable[_P, ResponseReturnValue]: ...

    @overload
    def login_required(
        self,
        view: None = None,
        /,
        *,
        on_missing: str | None = None,
    ) -> Callable[
        [Callable[_P, ResponseReturnValue]],
        Callable[_P, ResponseReturnValue],
    ]: ...

    def login_required(
        self,
        view: Callable[_P, ResponseReturnValue] | None = None,
        /,
        *,
        on_missing: str | None = None,
    ) -> (
        Callable[_P, ResponseReturnValue]
        | Callable[[Callable[_P, ResponseReturnValue]], Callable[_P, ResponseReturnValue]]
    ):
        # Exige autenticação, redirecionando requisições seguras ou levantando exceção
        if on_missing is not None and on_missing not in {"raise", "redirect"}:
            raise ValueError("on_missing must be 'redirect' or 'raise'")

        def decorate(
            function: Callable[_P, ResponseReturnValue],
        ) -> Callable[_P, ResponseReturnValue]:
            @wraps(function)
            def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> ResponseReturnValue:
                try:
                    _ = get_current_identity()
                except AuthenticationRequired:
                    return self._handle_unauthenticated(on_missing=on_missing)
                return function(*args, **kwargs)

            return wrapped

        if view is None:
            return decorate
        return decorate(view)

    def _handle_unauthenticated(self, *, on_missing: str | None) -> ResponseReturnValue:
        state = self._current_state()
        mode = state.config.unauthenticated_mode if on_missing is None else on_missing
        if mode == "raise" or request.method not in {"GET", "HEAD"}:
            error = AuthenticationRequired("authentication is required")
            state.observability.emit_error(error)
            raise error
        if not state.routes_registered:
            raise RuntimeError("authentication routes are not registered")

        target = request.full_path
        if target.endswith("?"):
            target = target[:-1]
        return redirect(url_for(f"{blueprint_name()}.login", next=target))

    def _notify_error(self, error: MicrosoftEntraAuthError) -> None:
        # Notifica hooks sobre erros levantados antes da execução de um método público da extensão
        self._current_state().observability.emit_error(error)

    def _current_state(self) -> _MicrosoftEntraAuthState:
        state = current_app.extensions.get(_EXTENSION_KEY)
        if not isinstance(state, _MicrosoftEntraAuthState) or state.extension is not self:
            raise RuntimeError("MicrosoftEntraAuth is not initialized for the current application")
        return state

    def _state_for_app(self, app: Flask) -> _MicrosoftEntraAuthState:
        state = app.extensions.get(_EXTENSION_KEY)
        if not isinstance(state, _MicrosoftEntraAuthState) or state.extension is not self:
            raise RuntimeError("MicrosoftEntraAuth is not initialized for this application")
        return state


def _elapsed_ms(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000


__all__ = ["AuthEvent", "MicrosoftEntraAuth"]
