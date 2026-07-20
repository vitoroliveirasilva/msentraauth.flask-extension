from __future__ import annotations

from typing import cast

from msal import (  # type: ignore[import-untyped]
    ConfidentialClientApplication,
    SerializableTokenCache,
)

from ..config import MicrosoftEntraAuthConfig
from .protocols import MsalClient


def create_confidential_client(
    config: MicrosoftEntraAuthConfig,
    token_cache: SerializableTokenCache,
) -> MsalClient:
    # Construir o cliente MSAL padrão apenas quando uma operação de autenticação precisar dele
    client = ConfidentialClientApplication(
        client_id=config.client_id,
        client_credential=config.client_secret,
        authority=config.authority,
        token_cache=token_cache,
        enable_pii_log=False,
    )
    return cast(MsalClient, client)
