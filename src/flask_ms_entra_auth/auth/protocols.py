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
