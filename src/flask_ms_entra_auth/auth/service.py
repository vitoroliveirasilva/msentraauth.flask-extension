from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ..config import MicrosoftEntraAuthConfig
from ..errors import (
    AuthenticationRequired,
    ConsentRequired,
    ProviderUnavailableError,
    TokenAcquisitionError,
)
from ..storage import AuthStorage
from .client import create_confidential_client
from .protocols import MsalAccount, MsalClientFactory, MsalResult
from .token_cache import load_token_cache, persist_token_cache


@dataclass(frozen=True, slots=True)
class MsalService:
    # Application-scoped MSAL orquestração sem estado de solicitação ou usuário. O serviço é imutável e não mantém estado de solicitação ou usuário. Ele é projetado para ser usado em um contexto de aplicativo Flask, onde a configuração e o armazenamento são fornecidos no nível do aplicativo

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
        # Retorna um token de acesso do lado do servidor do cache ou atualização silenciosa
        requested_scopes = _normalize_scopes(scopes, default=self.config.scopes)
        if not isinstance(force_refresh, bool):
            msg = "force_refresh must be a boolean"
            raise TypeError(msg)

        cache = load_token_cache(self.storage, home_account_id)
        try:
            client = self.client_factory(self.config, cache)
            accounts = client.get_accounts()
            account = _select_account(accounts, home_account_id)
            result = client.acquire_token_silent_with_error(
                list(requested_scopes),
                account,
                force_refresh=force_refresh,
            )
        except (AuthenticationRequired, ConsentRequired, TokenAcquisitionError):
            raise
        except Exception as exc:
            raise ProviderUnavailableError("Microsoft identity provider is unavailable") from exc
        finally:
            persist_token_cache(
                self.storage,
                home_account_id,
                cache,
                ttl=self.config.token_cache_ttl,
            )

        return _access_token_from_result(result)


def _select_account(accounts: Sequence[MsalAccount], home_account_id: str) -> MsalAccount:
    for account in accounts:
        candidate = account.get("home_account_id")
        if isinstance(candidate, str) and candidate == home_account_id:
            return account
    raise AuthenticationRequired("no matching MSAL account is available")


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
    if not isinstance(access_token, str) or not access_token:
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
