from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from flask import Blueprint, Response, redirect, request
from flask.typing import ResponseReturnValue
from werkzeug.wrappers import Response as WerkzeugResponse

from ..errors import (
    AuthenticationCancelled,
    AuthenticationRejected,
    AuthenticationRequired,
    ConfigurationError,
    HookExecutionError,
    InvalidCallbackError,
    InvalidNavigationTarget,
    LocalBindingError,
    MicrosoftEntraAuthError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)

if TYPE_CHECKING:
    from ..config import MicrosoftEntraAuthConfig
    from ..extension import MicrosoftEntraAuth

_BLUEPRINT_NAME = "ms_entra_auth"
_ResponseT = TypeVar("_ResponseT", bound=WerkzeugResponse)


def create_auth_blueprint(
    extension: MicrosoftEntraAuth,
    config: MicrosoftEntraAuthConfig,
) -> Blueprint:
    # Cria um blueprint Flask para lidar com rotas de autenticação e logout
    blueprint = Blueprint(_BLUEPRINT_NAME, __name__)

    @blueprint.get("/login")
    def login() -> ResponseReturnValue:
        return _execute_route(
            lambda: _secure_redirect(extension.begin_login(next_url=_single_query_value("next"))),
            extension=extension,
            handle_errors=config.handle_route_errors,
        )

    @blueprint.get("/callback")
    def callback() -> ResponseReturnValue:
        def complete() -> ResponseReturnValue:
            result = extension.complete_login(_single_value_query())
            return _secure_redirect(result.next_url)

        return _execute_route(
            complete,
            extension=extension,
            handle_errors=config.handle_route_errors,
        )

    @blueprint.post("/logout")
    def logout() -> ResponseReturnValue:
        return _execute_route(
            lambda: _secure_redirect(extension.logout()),
            extension=extension,
            handle_errors=config.handle_route_errors,
        )

    return blueprint


def blueprint_name() -> str:
    # Retorna o prefixo de endpoint estável usado pelo blueprint interno
    return _BLUEPRINT_NAME


def _single_query_value(name: str) -> str | None:
    values = request.args.getlist(name)
    if not values:
        return None
    if len(values) != 1:
        raise InvalidNavigationTarget("navigation target must appear at most once")
    return values[0]


def _single_value_query() -> dict[str, str]:
    response: dict[str, str] = {}
    for key, values in request.args.lists():
        if len(values) != 1:
            raise InvalidCallbackError("authentication callback contains duplicate fields")
        response[key] = values[0]
    return response


def _execute_route(
    operation: Callable[[], ResponseReturnValue],
    *,
    extension: MicrosoftEntraAuth,
    handle_errors: bool,
) -> ResponseReturnValue:
    try:
        return operation()
    except MicrosoftEntraAuthError as exc:
        extension._notify_error(exc)
        if not handle_errors:
            raise
        return _safe_error_response(exc)


def _secure_redirect(location: str) -> WerkzeugResponse:
    return _apply_security_headers(redirect(location))


def _safe_error_response(error: MicrosoftEntraAuthError) -> Response:
    status, message = _error_status_and_message(error)
    response = Response(message, status=status, content_type="text/plain; charset=utf-8")
    return _apply_security_headers(response)


def _apply_security_headers(response: _ResponseT) -> _ResponseT:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error_status_and_message(error: MicrosoftEntraAuthError) -> tuple[int, str]:
    if isinstance(error, AuthenticationCancelled):
        return 400, "Authentication was cancelled."
    if isinstance(error, InvalidCallbackError | InvalidNavigationTarget):
        return 400, "Authentication request is invalid or expired."
    if isinstance(error, AuthenticationRejected):
        return 403, "Authentication was rejected by the application."
    if isinstance(error, AuthenticationRequired):
        return 401, "Authentication is required."
    if isinstance(error, TokenAcquisitionError):
        return 502, "Authentication could not be completed."
    if isinstance(
        error,
        ProviderUnavailableError | StorageError | LocalBindingError | HookExecutionError,
    ):
        return 503, "Authentication service is temporarily unavailable."
    if isinstance(error, ConfigurationError):
        return 500, "Authentication is not configured correctly."
    return 400, "Authentication could not be completed."
