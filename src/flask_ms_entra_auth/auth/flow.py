from __future__ import annotations

import hmac
import json
from collections.abc import Iterable, Mapping, Sequence
from secrets import token_urlsafe
from typing import Final, cast
from urllib.parse import urlsplit

from msal import SerializableTokenCache  # type: ignore[import-untyped]

from ..config import MicrosoftEntraAuthConfig
from ..errors import (
    AuthenticationCancelled,
    IdentityValidationError,
    InvalidCallbackError,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from ..identity import Identity
from ..storage import AtomicAuthStorage, AuthStorage
from ..web.models import LoginResult, LoginStart
from .protocols import InteractiveMsalClient, MsalAccount, MsalClientFactory, MsalResult
from .token_cache import persist_token_cache

_FLOW_VERSION: Final = 1
_RANDOM_BYTES: Final = 32
_MAX_FLOW_ID_LENGTH: Final = 128
_MAX_CALLBACK_FIELDS: Final = 32
_MAX_CALLBACK_VALUE_LENGTH: Final = 8_192


class AuthCodeFlowService:
    # Inicia e conclui transações de código de autorização MSAL de uso único

    __slots__ = ("_client_factory", "_config", "_storage")

    def __init__(
        self,
        *,
        config: MicrosoftEntraAuthConfig,
        storage: AuthStorage,
        client_factory: MsalClientFactory,
    ) -> None:
        self._config = config
        self._storage = storage
        self._client_factory = client_factory

    def begin_login(
        self,
        *,
        next_url: str,
        scopes: Iterable[str] | None = None,
    ) -> LoginStart:
        # Cria e persiste uma transação de login interativa
        requested_scopes = _normalize_scopes(scopes, default=self._config.scopes)
        state = token_urlsafe(_RANDOM_BYTES)
        cache = SerializableTokenCache()
        try:
            client = cast(InteractiveMsalClient, self._client_factory(self._config, cache))
            flow = client.initiate_auth_code_flow(
                list(requested_scopes),
                redirect_uri=self._config.redirect_uri,
                state=state,
            )
        except Exception as exc:
            raise ProviderUnavailableError("Microsoft identity provider is unavailable") from exc

        validated_flow = _validate_initiated_flow(
            flow,
            expected_state=state,
            expected_authority=self._config.authority,
        )
        flow_id = token_urlsafe(_RANDOM_BYTES)
        payload = _serialize_flow(validated_flow, next_url=next_url)
        self._storage.save(_flow_key(flow_id), payload, ttl=self._config.flow_ttl)
        return LoginStart(auth_uri=_flow_auth_uri(validated_flow), flow_id=flow_id)

    def complete_login(
        self,
        *,
        flow_id: str,
        auth_response: Mapping[str, object],
    ) -> LoginResult:
        # Consome uma transação, valide o callback e construa uma identidade
        validated_flow_id = _validate_flow_id(flow_id)
        key = _flow_key(validated_flow_id)

        if isinstance(self._storage, AtomicAuthStorage):
            payload = self._storage.take(key)
        else:
            payload = self._storage.load(key)
            if payload is not None:
                self._storage.delete(key)

        if payload is None:
            raise InvalidCallbackError("authentication flow is missing, expired, or consumed")

        # Consome antes da redenção para que tentativas de repetição e callbacks simultâneos não possam reproduzi-lo
        flow, next_url = _deserialize_flow(payload)
        response = _normalize_auth_response(auth_response)
        _validate_callback_state(flow, response)

        if response.get("error") == "access_denied":
            raise AuthenticationCancelled("authentication was cancelled")
        if "error" in response:
            raise TokenAcquisitionError(
                "interactive token acquisition failed",
                code=_safe_metadata(response.get("error")),
                correlation_id=_safe_metadata(response.get("correlation_id"), maximum=128),
            )

        cache = SerializableTokenCache()
        try:
            client = cast(InteractiveMsalClient, self._client_factory(self._config, cache))
            result = client.acquire_token_by_auth_code_flow(flow, response)
        except ValueError as exc:
            raise InvalidCallbackError("authentication callback validation failed") from exc
        except Exception as exc:
            raise ProviderUnavailableError("Microsoft identity provider is unavailable") from exc

        validated_result = _validate_interactive_result(result)
        claims = validated_result.get("id_token_claims")
        if not isinstance(claims, Mapping):
            raise InvalidCallbackError(
                "authentication result did not contain valid identity claims"
            )

        try:
            account = _select_authenticated_account(client.get_accounts(), claims)
            home_account_id = _account_home_id(account)
            identity = Identity.from_claims(
                claims,
                home_account_id=home_account_id,
                expected_tenant_id=self._config.tenant_id,
            )
        except IdentityValidationError:
            raise
        except (TypeError, ValueError) as exc:
            raise InvalidCallbackError("authenticated account could not be resolved") from exc
        except Exception as exc:
            raise ProviderUnavailableError("Microsoft identity provider is unavailable") from exc

        persist_token_cache(
            self._storage,
            home_account_id,
            cache,
            ttl=self._config.token_cache_ttl,
        )
        return LoginResult(identity=identity, next_url=next_url)

    def discard(self, flow_id: str) -> None:
        # Deleta uma transação pendente quando a sessão do navegador a abandona
        self._storage.delete(_flow_key(_validate_flow_id(flow_id)))


def _validate_initiated_flow(
    flow: MsalResult,
    *,
    expected_state: str,
    expected_authority: str,
) -> Mapping[str, object]:
    if not isinstance(flow, Mapping):
        raise TokenAcquisitionError("MSAL returned an invalid authentication flow")
    if "error" in flow:
        raise TokenAcquisitionError(
            "interactive authentication could not be started",
            code=_safe_metadata(flow.get("error")),
            correlation_id=_safe_metadata(flow.get("correlation_id"), maximum=128),
        )

    state = flow.get("state")
    if not isinstance(state, str) or not hmac.compare_digest(state, expected_state):
        raise TokenAcquisitionError("MSAL returned an inconsistent authentication flow")
    _ = _flow_auth_uri(flow, expected_authority=expected_authority)
    _ensure_json_compatible(flow)
    return flow


def _flow_auth_uri(
    flow: Mapping[str, object],
    *,
    expected_authority: str | None = None,
) -> str:
    auth_uri = flow.get("auth_uri")
    if not isinstance(auth_uri, str) or len(auth_uri) > 8_192:
        raise TokenAcquisitionError("MSAL returned no valid authorization URI")
    try:
        parsed = urlsplit(auth_uri)
    except ValueError:
        raise TokenAcquisitionError("MSAL returned no valid authorization URI") from None
    try:
        _ = parsed.port
    except ValueError:
        raise TokenAcquisitionError("MSAL returned no valid authorization URI") from None
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise TokenAcquisitionError("MSAL returned no valid authorization URI")
    if expected_authority is not None:
        authority = urlsplit(expected_authority)
        if parsed.netloc.casefold() != authority.netloc.casefold():
            raise TokenAcquisitionError("MSAL returned an unexpected authorization host")
    return auth_uri


def _serialize_flow(flow: Mapping[str, object], *, next_url: str) -> bytes:
    payload = {"version": _FLOW_VERSION, "flow": flow, "next_url": next_url}
    try:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise StorageError("authentication flow could not be serialized") from exc


def _deserialize_flow(payload: bytes) -> tuple[Mapping[str, object], str]:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise StorageError("stored authentication flow could not be decoded") from exc
    if not isinstance(data, Mapping) or data.get("version") != _FLOW_VERSION:
        raise StorageError("stored authentication flow has an invalid structure")
    flow = data.get("flow")
    next_url = data.get("next_url")
    if not isinstance(flow, Mapping) or not isinstance(next_url, str):
        raise StorageError("stored authentication flow has an invalid structure")
    _ensure_json_compatible(flow)
    return flow, next_url


def _normalize_auth_response(auth_response: Mapping[str, object]) -> dict[str, str]:
    if not isinstance(auth_response, Mapping) or len(auth_response) > _MAX_CALLBACK_FIELDS:
        raise InvalidCallbackError("authentication callback has an invalid structure")

    normalized: dict[str, str] = {}
    for key, value in auth_response.items():
        if (
            not isinstance(key, str)
            or not key
            or len(key) > 128
            or not isinstance(value, str)
            or len(value) > _MAX_CALLBACK_VALUE_LENGTH
            or any(ord(character) < 32 for character in key)
        ):
            raise InvalidCallbackError("authentication callback has an invalid structure")
        normalized[key] = value
    return normalized


def _validate_callback_state(
    flow: Mapping[str, object],
    response: Mapping[str, str],
) -> None:
    expected = flow.get("state")
    received = response.get("state")
    if (
        not isinstance(expected, str)
        or not isinstance(received, str)
        or not hmac.compare_digest(expected, received)
    ):
        raise InvalidCallbackError("authentication callback state is invalid")


def _validate_interactive_result(result: MsalResult) -> Mapping[str, object]:
    if not isinstance(result, Mapping):
        raise InvalidCallbackError("MSAL returned an invalid authentication result")
    if "error" in result:
        raise TokenAcquisitionError(
            "interactive token acquisition failed",
            code=_safe_metadata(result.get("error")),
            correlation_id=_safe_metadata(result.get("correlation_id"), maximum=128),
        )
    return result


def _select_authenticated_account(
    accounts: Sequence[MsalAccount],
    claims: Mapping[str, object],
) -> MsalAccount:
    object_id = claims.get("oid")
    tenant_id = claims.get("tid")
    if not isinstance(object_id, str) or not isinstance(tenant_id, str):
        raise ValueError("identity claims are incomplete")

    matches: list[MsalAccount] = []
    for account in accounts:
        local_account_id = account.get("local_account_id")
        realm = account.get("realm", account.get("tenant_id"))
        if (
            isinstance(local_account_id, str)
            and isinstance(realm, str)
            and local_account_id == object_id
            and realm.casefold() == tenant_id.casefold()
        ):
            matches.append(account)
    if len(matches) != 1:
        raise ValueError("authenticated account is ambiguous or missing")
    return matches[0]


def _account_home_id(account: MsalAccount) -> str:
    value = account.get("home_account_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("authenticated account has no home account ID")
    return value.strip()


def _normalize_scopes(
    scopes: Iterable[str] | None,
    *,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    if scopes is None:
        return default
    if isinstance(scopes, str):
        raise TypeError("scopes must be a non-string iterable")

    normalized: list[str] = []
    seen: set[str] = set()
    for scope in scopes:
        if not isinstance(scope, str):
            raise TypeError("scope entries must be strings")
        clean_scope = scope.strip()
        if not clean_scope:
            raise ValueError("scope entries must be non-empty")
        if clean_scope not in seen:
            normalized.append(clean_scope)
            seen.add(clean_scope)
    if not normalized:
        raise ValueError("at least one scope is required")
    return tuple(normalized)


def _validate_flow_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > _MAX_FLOW_ID_LENGTH
        or any(not (character.isalnum() or character in "_-") for character in value)
    ):
        raise InvalidCallbackError("authentication flow identifier is invalid")
    return value


def _flow_key(flow_id: str) -> str:
    return f"flow:{flow_id}"


def _ensure_json_compatible(value: object, *, depth: int = 0) -> None:
    if depth > 12:
        raise StorageError("authentication flow is too deeply nested")
    if value is None or isinstance(value, str | int | float | bool):
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise StorageError("authentication flow contains invalid data")
            _ensure_json_compatible(item, depth=depth + 1)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _ensure_json_compatible(item, depth=depth + 1)
        return
    raise StorageError("authentication flow contains invalid data")


def _safe_metadata(value: object, *, maximum: int = 64) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        return None
    if any(not (character.isalnum() or character in "._-") for character in normalized):
        return None
    return normalized
