from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Protocol, TypeAlias

from msal import SerializableTokenCache  # type: ignore[import-untyped]

from ..config import MicrosoftEntraAuthConfig

MsalAccount: TypeAlias = Mapping[str, object]
MsalResult: TypeAlias = Mapping[str, object]


class MsalClient(Protocol):
    # Subconjunto de um cliente MSAL confidencial necessário para a aquisição silenciosa

    def get_accounts(self, username: str | None = None) -> Sequence[MsalAccount]:
        # Retorna as contas atualmente representadas no cache de tokens
        ...


class InteractiveMsalClient(MsalClient, Protocol):
    # Subconjunto de um cliente MSAL confidencial necessário para operações interativas do fluxo de código de autorização

    def initiate_auth_code_flow(
        self,
        scopes: list[str],
        *,
        redirect_uri: str,
        state: str,
    ) -> MsalResult:
        # Cria uma transação de fluxo de código de autorização
        ...

    def acquire_token_by_auth_code_flow(
        self,
        auth_code_flow: Mapping[str, object],
        auth_response: Mapping[str, str],
    ) -> MsalResult:
        # Valida um callback e resgata seu código de autorização
        ...


class SilentMsalClient(MsalClient, Protocol):
    # Subconjunto de um cliente MSAL confidencial necessário para a aquisição silenciosa

    def acquire_token_silent_with_error(
        self,
        scopes: list[str],
        account: MsalAccount,
        *,
        force_refresh: bool = False,
    ) -> MsalResult | None:
        # Adquire um token silenciosamente enquanto preserva os detalhes do erro de atualização
        ...


MsalClientFactory: TypeAlias = Callable[
    [MicrosoftEntraAuthConfig, SerializableTokenCache],
    MsalClient,
]
