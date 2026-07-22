from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from msal import SerializableTokenCache  # type: ignore[import-untyped]

from ..config import MicrosoftEntraAuthConfig
from ..errors import (
    AuthenticationRequired,
    ConsentRequired,
    ProviderUnavailableError,
    StorageError,
    TokenAcquisitionError,
)
from ..storage import AuthStorage
from .client import create_confidential_client
from .protocols import MsalAccount, MsalClientFactory, MsalResult, SilentMsalClient
from .token_cache import load_token_cache, persist_token_cache


@dataclass(frozen=True, slots=True)
class MsalService:
    # Orquestração MSAL no escopo do aplicativo sem estado de solicitação ou usuário

    config: MicrosoftEntraAuthConfig
    storage: AuthStorage
    client_factory: MsalClientFactory = create_confidential_client

    def acquire_token_silent(
        self,
        *,
        home_account_id: str,
        scopes: Iterable[str] | None = None,
        force_refresh: bool = False,
    ) -> str:
        # Retorna um token de acesso server-side do cache ou atualização silenciosa
        requested_scopes = _normalize_scopes(scopes, default=self.config.scopes)
        if not isinstance(force_refresh, bool):
            msg = "force_refresh must be a boolean"
            raise TypeError(msg)

        cache = load_token_cache(self.storage, home_account_id)
        try:
            client = cast(SilentMsalClient, self.client_factory(self.config, cache))
            accounts = client.get_accounts()
            account = _select_account(accounts, home_account_id)
            result = client.acquire_token_silent_with_error(
                list(requested_scopes),
                account,
                force_refresh=force_refresh,
            )
            token = _access_token_from_result(result)
        except (AuthenticationRequired, ConsentRequired, TokenAcquisitionError) as exc:
            _persist_cache_after_failure(
                self.storage,
                home_account_id,
                cache,
                ttl=self.config.token_cache_ttl,
                primary_error=exc,
            )
            raise
        except Exception as exc:
            provider_error = ProviderUnavailableError("Microsoft identity provider is unavailable")
            _persist_cache_after_failure(
                self.storage,
                home_account_id,
                cache,
                ttl=self.config.token_cache_ttl,
                primary_error=provider_error,
            )
            raise provider_error from exc

        persist_token_cache(
            self.storage,
            home_account_id,
            cache,
            ttl=self.config.token_cache_ttl,
        )
        return token


def _persist_cache_after_failure(
    storage: AuthStorage,
    home_account_id: str,
    cache: SerializableTokenCache,
    *,
    ttl: int,
    primary_error: Exception,
) -> None:
    try:
        persist_token_cache(storage, home_account_id, cache, ttl=ttl)
    except StorageError:
        primary_error.add_note("token cache persistence also failed")


def _select_account(accounts: Sequence[MsalAccount], home_account_id: str) -> MsalAccount:
    matches: list[MsalAccount] = []
    for account in accounts:
        candidate = account.get("home_account_id")
        if isinstance(candidate, str) and candidate == home_account_id:
            matches.append(account)
    if not matches:
        raise AuthenticationRequired("no matching MSAL account is available")
    if len(matches) != 1:
        raise AuthenticationRequired("multiple matching MSAL accounts are available")
    return matches[0]


def _access_token_from_result(result: MsalResult | None) -> str:
    if result is None:
        raise ConsentRequired("interactive authentication is required")
    if not isinstance(result, Mapping):
        raise TokenAcquisitionError("MSAL returned an invalid token result")

    error = result.get("error")
    if error is not None:
        raise TokenAcquisitionError(
            "silent token acquisition failed",
            code=_safe_metadata(error),
            correlation_id=_safe_metadata(result.get("correlation_id"), maximum=128),
        )

    access_token = result.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise TokenAcquisitionError("MSAL returned no access token")
    return access_token


def _normalize_scopes(
    scopes: Iterable[str] | None,
    *,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    if scopes is None:
        return default
    if isinstance(scopes, str):
        msg = "scopes must be a non-string iterable"
        raise TypeError(msg)

    normalized: list[str] = []
    seen: set[str] = set()
    for scope in scopes:
        if not isinstance(scope, str):
            msg = "scope entries must be strings"
            raise TypeError(msg)
        clean_scope = scope.strip()
        if not clean_scope:
            raise ValueError("scope entries must be non-empty")
        if clean_scope not in seen:
            normalized.append(clean_scope)
            seen.add(clean_scope)
    if not normalized:
        raise ValueError("at least one scope is required")
    return tuple(normalized)


def _safe_metadata(value: object, *, maximum: int = 64) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        return None
    if any(not (character.isalnum() or character in "._-") for character in normalized):
        return None
    return normalized
