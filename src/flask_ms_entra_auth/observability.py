from __future__ import annotations

import logging
from secrets import token_hex
from time import time

from flask import g, has_request_context, request

from .config import MicrosoftEntraAuthConfig
from .errors import MicrosoftEntraAuthError, TokenAcquisitionError
from .hooks import _EVENT_LOG_MESSAGE, AuthEvent, HookRegistry

_REQUEST_ID_ATTRIBUTE = "_ms_entra_auth_request_id"
_MAX_REQUEST_ID_LENGTH = 128


class Observability:
    # Encapsula a lógica de observabilidade, incluindo a emissão de eventos e o registro estruturado, para fornecer insights sobre o comportamento da extensão de autenticação do Microsoft Entra em aplicativos Flask

    __slots__ = ("_config", "_hooks", "_logger")

    def __init__(
        self,
        config: MicrosoftEntraAuthConfig,
        hooks: HookRegistry,
        logger: logging.Logger,
    ) -> None:
        self._config = config
        self._hooks = hooks
        self._logger = logger

    def emit(
        self,
        name: str,
        *,
        duration_ms: float | None = None,
        error: MicrosoftEntraAuthError | None = None,
    ) -> AuthEvent:
        # Cria e despacha um evento contendo apenas metadados normalizados, garantindo que informações sensíveis não sejam expostas nos logs ou hooks de eventos
        endpoint: str | None = None
        method: str | None = None
        request_id: str | None = None
        if has_request_context():
            endpoint = request.endpoint
            method = request.method
            request_id = self._request_id()

        correlation_id = None
        if isinstance(error, TokenAcquisitionError):
            correlation_id = error.correlation_id

        event = AuthEvent(
            name=name,
            timestamp=time(),
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            duration_ms=(None if duration_ms is None else round(max(duration_ms, 0.0), 3)),
            error_code=None if error is None else type(error).__name__,
            correlation_id=correlation_id,
        )
        hook_failures = self._hooks.emit_event(event)
        if self._config.event_logging:
            self._logger.info(
                _EVENT_LOG_MESSAGE,
                extra={
                    "auth_event": event.name,
                    "auth_request_id": event.request_id,
                    "auth_endpoint": event.endpoint,
                    "auth_method": event.method,
                    "auth_duration_ms": event.duration_ms,
                    "auth_error_code": event.error_code,
                    "auth_correlation_id": event.correlation_id,
                    "auth_hook_failures": hook_failures,
                },
            )
        return event

    def emit_error(self, error: MicrosoftEntraAuthError) -> None:
        # Notifica os hooks de erro apenas uma vez e emite um evento de falha sanitizado, garantindo que informações sensíveis não sejam expostas nos logs ou hooks de eventos
        if getattr(error, "_ms_entra_auth_notified", False):
            return
        error._ms_entra_auth_notified = True
        hook_failures = self._hooks.emit_error(error)
        event_name = _error_event_name(error)
        event = self.emit(event_name, error=error)
        if self._config.event_logging and hook_failures:
            self._logger.warning(
                _EVENT_LOG_MESSAGE,
                extra={
                    "auth_event": "error_hook_failed",
                    "auth_request_id": event.request_id,
                    "auth_endpoint": event.endpoint,
                    "auth_method": event.method,
                    "auth_duration_ms": None,
                    "auth_error_code": type(error).__name__,
                    "auth_correlation_id": event.correlation_id,
                    "auth_hook_failures": hook_failures,
                },
            )

    def _request_id(self) -> str:
        existing = getattr(g, _REQUEST_ID_ATTRIBUTE, None)
        if isinstance(existing, str):
            return existing

        candidate = request.headers.get(self._config.request_id_header)
        request_id = _safe_request_id(candidate) or token_hex(16)
        setattr(g, _REQUEST_ID_ATTRIBUTE, request_id)
        return request_id


def _safe_request_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > _MAX_REQUEST_ID_LENGTH
        or any(not (character.isalnum() or character in "._:-") for character in normalized)
    ):
        return None
    return normalized


def _error_event_name(error: MicrosoftEntraAuthError) -> str:
    name = type(error).__name__
    if name == "AuthenticationCancelled":
        return "authentication_cancelled"
    if name == "AuthenticationRejected":
        return "authentication_rejected"
    if name == "StorageError":
        return "storage_failure"
    return "authentication_error"
