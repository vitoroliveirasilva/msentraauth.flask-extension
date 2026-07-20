from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Final, TypeVar

from .errors import (
    AuthenticationRejected,
    HookExecutionError,
    LocalBindingError,
    MicrosoftEntraAuthError,
)
from .identity import Identity

AuthenticatedHook = Callable[[Identity], None]
LogoutHook = Callable[[Identity | None], None]
ErrorHook = Callable[[MicrosoftEntraAuthError], None]
_H = TypeVar("_H", bound=Callable[..., object])


@dataclass(frozen=True, slots=True)
class AuthEvent:
    # Sanitização e anonimização de informações sensíveis, como chaves secretas, para evitar vazamentos de dados nos eventos de autenticação emitidos pela extensão

    name: str
    timestamp: float
    request_id: str | None = None
    endpoint: str | None = None
    method: str | None = None
    duration_ms: float | None = None
    error_code: str | None = None
    correlation_id: str | None = None


EventHook = Callable[[AuthEvent], None]


class HookRegistry:
    # Encapsula a lógica de registro e execução de hooks de eventos, garantindo que os hooks sejam executados de forma segura e consistente, mesmo em cenários concorrentes

    __slots__ = ("_authenticated", "_errors", "_events", "_lock", "_logout")

    def __init__(self) -> None:
        self._authenticated: list[AuthenticatedHook] = []
        self._logout: list[LogoutHook] = []
        self._errors: list[ErrorHook] = []
        self._events: list[EventHook] = []
        self._lock = RLock()

    def on_authenticated(self, callback: AuthenticatedHook) -> AuthenticatedHook:
        # Registra um hook de autenticação bem-sucedida, permitindo que os desenvolvedores adicionem lógica personalizada que será executada após a autenticação do usuário, sem expor informações sensíveis
        return self._register(self._authenticated, callback)

    def on_logout(self, callback: LogoutHook) -> LogoutHook:
        # Registra um hook de logout local, permitindo que os desenvolvedores adicionem lógica personalizada que será executada após o logout do usuário, sem expor informações sensíveis
        return self._register(self._logout, callback)

    def on_error(self, callback: ErrorHook) -> ErrorHook:
        # Registra um hook de erro previsível, permitindo que os desenvolvedores adicionem lógica personalizada que será executada quando ocorrer um erro durante o processo de autenticação, sem expor informações sensíveis
        return self._register(self._errors, callback)

    def on_event(self, callback: EventHook) -> EventHook:
        # Registra um hook de evento estruturado sanitizado, permitindo que os desenvolvedores adicionem lógica personalizada que será executada quando um evento de autenticação ocorrer, garantindo que apenas metadados normalizados sejam expostos, sem informações sensíveis
        return self._register(self._events, callback)

    def emit_authenticated(self, identity: Identity) -> None:
        # Executa os hooks de vinculação local antes que a sessão do navegador seja estabelecida, garantindo que a identidade autenticada seja vinculada de forma segura ao contexto local, sem expor informações sensíveis
        for callback in self._snapshot(self._authenticated):
            try:
                callback(identity)
            except AuthenticationRejected:
                raise
            except Exception as exc:
                raise LocalBindingError(
                    "authenticated identity could not be bound locally",
                    event="authenticated",
                ) from exc

    def emit_logout(self, identity: Identity | None) -> None:
        # Executa os hooks de logout após o estado de autenticação local ser removido, garantindo que qualquer lógica personalizada relacionada ao logout seja executada de forma segura, sem expor informações sensíveis
        for callback in self._snapshot(self._logout):
            try:
                callback(identity)
            except Exception as exc:
                raise HookExecutionError("logout hook failed", event="logout") from exc

    def emit_error(self, error: MicrosoftEntraAuthError) -> int:
        # Executa os hooks de erro sem permitir que eles substituam o erro original, garantindo que a lógica personalizada relacionada a erros seja executada de forma segura, sem expor informações sensíveis
        failures = 0
        for callback in self._snapshot(self._errors):
            try:
                callback(error)
            except Exception:
                failures += 1
        return failures

    def emit_event(self, event: AuthEvent) -> int:
        # Executa os hooks de evento sem afetar o comportamento da autenticação, garantindo que a lógica personalizada relacionada a eventos seja executada de forma segura, sem expor informações sensíveis
        failures = 0
        for callback in self._snapshot(self._events):
            try:
                callback(event)
            except Exception:
                failures += 1
        return failures

    def _register(self, collection: list[_H], callback: _H) -> _H:
        if not callable(callback):
            raise TypeError("hook must be callable")
        with self._lock:
            if callback not in collection:
                collection.append(callback)
        return callback

    def _snapshot(self, collection: list[_H]) -> tuple[_H, ...]:
        with self._lock:
            return tuple(collection)


_EVENT_LOG_MESSAGE: Final = "flask_ms_entra_auth event"
