from __future__ import annotations

from dataclasses import dataclass

from ..identity import Identity


@dataclass(frozen=True, slots=True)
class LoginStart:
    # Resultado server-side da inicialização de uma transação de login interativo

    auth_uri: str
    flow_id: str


@dataclass(frozen=True, slots=True)
class LoginResult:
    # Resultado validado da conclusão de uma transação de login interativo

    identity: Identity
    next_url: str
