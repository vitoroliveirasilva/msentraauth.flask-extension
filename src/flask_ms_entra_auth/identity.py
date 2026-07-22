from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Final

from .errors import IdentityValidationError

_FORBIDDEN_CLAIM_KEYS: Final = frozenset(
    {
        "access_token",
        "client_secret",
        "id_token",
        "refresh_token",
        "token_cache",
    }
)
_MAX_CLAIM_DEPTH: Final = 12


@dataclass(frozen=True, slots=True, repr=False)
class Identity:
    # Valida identidade para uma autenticação MS Entra Account

    object_id: str
    tenant_id: str
    home_account_id: str
    subject: str | None = None
    display_name: str | None = None
    username: str | None = None
    claims: Mapping[str, object] = field(default_factory=dict, compare=True)

    def __post_init__(self) -> None:
        object.__setattr__(self, "object_id", _required_text("oid", self.object_id))
        object.__setattr__(self, "tenant_id", _required_text("tid", self.tenant_id))
        object.__setattr__(
            self,
            "home_account_id",
            _required_text("home_account_id", self.home_account_id),
        )
        object.__setattr__(self, "subject", _optional_text("sub", self.subject))
        object.__setattr__(self, "display_name", _optional_text("name", self.display_name))
        object.__setattr__(
            self,
            "username",
            _optional_text("preferred_username", self.username),
        )
        object.__setattr__(self, "claims", _freeze_claims(self.claims))

    @classmethod
    def from_claims(
        cls,
        claims: Mapping[str, object],
        *,
        home_account_id: str,
        expected_tenant_id: str | None = None,
    ) -> Identity:
        # Construtor de identidade a partir de claims do token de ID e um identificador de conta MSAL
        frozen_claims = _freeze_claims(claims)
        tenant_id = _required_claim_text(frozen_claims, "tid")
        if (
            expected_tenant_id is not None
            and tenant_id.casefold()
            != _required_text("expected_tenant_id", expected_tenant_id).casefold()
        ):
            raise IdentityValidationError("identity tenant does not match configured tenant")

        return cls(
            object_id=_required_claim_text(frozen_claims, "oid"),
            tenant_id=tenant_id,
            home_account_id=home_account_id,
            subject=_optional_claim_text(frozen_claims, "sub"),
            display_name=_optional_claim_text(frozen_claims, "name"),
            username=_first_claim_text(frozen_claims, "preferred_username", "upn"),
            claims=frozen_claims,
        )

    @property
    def stable_id(self) -> tuple[str, str]:
        # Retorna uma tupla (tenant_id, object_id) que pode ser usada para identificar de forma única a identidade do usuário dentro do contexto da aplicação
        return (self.tenant_id, self.object_id)

    def __repr__(self) -> str:
        # Retorna a representação da identidade sem expor claims ou dados pessoais
        return "Identity(authenticated=True)"


def _required_claim_text(claims: Mapping[str, object], key: str) -> str:
    value = claims.get(key)
    if not isinstance(value, str) or not value.strip():
        raise IdentityValidationError(
            f"identity claim '{key}' must be a non-empty string when required"
        )
    return value.strip()


def _optional_claim_text(claims: Mapping[str, object], key: str) -> str | None:
    value = claims.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise IdentityValidationError(
            f"identity claim '{key}' must be a non-empty string when optional"
        )
    return value.strip()


def _first_claim_text(claims: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = claims.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise IdentityValidationError(
                f"identity claim '{key}' must be a non-empty string when present"
            )
        return value.strip()
    return None


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IdentityValidationError(f"identity field '{name}' must be a non-empty string")
    return value.strip()


def _optional_text(name: str, value: object | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise IdentityValidationError(
            f"identity field '{name}' must be a non-empty string when present"
        )
    return value.strip()


def _freeze_claims(claims: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(claims, Mapping):
        raise IdentityValidationError("identity claims must be a mapping")

    frozen: dict[str, object] = {}
    for key, value in claims.items():
        if not isinstance(key, str) or not key:
            raise IdentityValidationError("identity claim names must be non-empty strings")
        if key.casefold() in _FORBIDDEN_CLAIM_KEYS:
            raise IdentityValidationError("identity claims must not contain credentials")
        frozen[key] = _freeze_claim_value(value, depth=1)
    return MappingProxyType(frozen)


def _freeze_claim_value(value: object, *, depth: int) -> object:
    if depth > _MAX_CLAIM_DEPTH:
        raise IdentityValidationError("identity claims are too deeply nested")
    if isinstance(value, float) and not isfinite(value):
        raise IdentityValidationError("identity claims must contain finite numeric values")
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        nested: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise IdentityValidationError(
                    "nested identity claim names must be non-empty strings"
                )
            if key.casefold() in _FORBIDDEN_CLAIM_KEYS:
                raise IdentityValidationError("identity claims must not contain credentials")
            nested[key] = _freeze_claim_value(item, depth=depth + 1)
        return MappingProxyType(nested)
    if isinstance(value, list | tuple):
        return tuple(_freeze_claim_value(item, depth=depth + 1) for item in value)
    raise IdentityValidationError("identity claims must contain only JSON-compatible values")
