from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from ipaddress import ip_address
from typing import Final
from urllib.parse import SplitResult, urlsplit

from .errors import ConfigurationError

_DEFAULT_AUTHORITY_HOST: Final = "login.microsoftonline.com"
_DEFAULT_SCOPES: Final = ("User.Read",)
_RESERVED_TENANTS: Final = frozenset({"common", "consumers", "organizations"})
_PLACEHOLDERS: Final = frozenset(
    {
        "...",
        "changeme",
        "change-me",
        "replace-me",
        "replace_me",
        "todo",
        "your-client-id",
        "your-client-secret",
        "your-tenant-id",
        "your-value-here",
    }
)


@dataclass(frozen=True, slots=True)
class MicrosoftEntraAuthConfig:
    # Validação e imautabilidade da configuração do Microsoft Entra Auth para uma aplicação Flask

    client_id: str
    client_secret: str = field(repr=False)
    tenant_id: str
    redirect_uri: str
    authority: str
    scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfigOverrides:
    # Imutabilidade dos valores de nível de construtor com precedência sobre ``app.config``.

    client_id: str | None = None
    client_secret: str | None = None
    tenant_id: str | None = None
    redirect_uri: str | None = None
    authority: str | None = None
    scopes: Iterable[str] | None = None


def resolve_config(
    app_config: Mapping[str, object], overrides: ConfigOverrides
) -> MicrosoftEntraAuthConfig:
    # Resolve constructor overrides, Flask configuration e safe defaults

    client_id = _required_text(
        "MS_ENTRA_CLIENT_ID",
        _pick(overrides.client_id, app_config, "MS_ENTRA_CLIENT_ID"),
    )
    client_secret = _required_text(
        "MS_ENTRA_CLIENT_SECRET",
        _pick(overrides.client_secret, app_config, "MS_ENTRA_CLIENT_SECRET"),
    )
    tenant_id = _validate_tenant(
        _required_text(
            "MS_ENTRA_TENANT_ID",
            _pick(overrides.tenant_id, app_config, "MS_ENTRA_TENANT_ID"),
        )
    )
    redirect_uri = _validate_redirect_uri(
        _required_text(
            "MS_ENTRA_REDIRECT_URI",
            _pick(overrides.redirect_uri, app_config, "MS_ENTRA_REDIRECT_URI"),
        )
    )

    authority_value = _pick(overrides.authority, app_config, "MS_ENTRA_AUTHORITY")
    authority = (
        _default_authority(tenant_id)
        if authority_value is None
        else _validate_authority(_required_text("MS_ENTRA_AUTHORITY", authority_value), tenant_id)
    )

    scopes_value = _pick(overrides.scopes, app_config, "MS_ENTRA_SCOPES")
    scopes = _validate_scopes(_DEFAULT_SCOPES if scopes_value is None else scopes_value)

    return MicrosoftEntraAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
        redirect_uri=redirect_uri,
        authority=authority,
        scopes=scopes,
    )


def _pick(
    override: object | None,
    app_config: Mapping[str, object],
    key: str,
) -> object | None:
    if override is not None:
        return override
    return app_config.get(key)


def _required_text(key: str, value: object | None) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{key} must be a non-empty string")

    normalized = value.strip()
    if not normalized or _is_placeholder(normalized):
        raise ConfigurationError(f"{key} must be configured with a real value")
    return normalized


def _is_placeholder(value: str) -> bool:
    normalized = value.casefold()
    return (
        normalized in _PLACEHOLDERS
        or (normalized.startswith("<") and normalized.endswith(">"))
        or (normalized.startswith("{{") and normalized.endswith("}}"))
    )


def _validate_tenant(tenant_id: str) -> str:
    normalized = tenant_id.casefold()
    if normalized in _RESERVED_TENANTS:
        raise ConfigurationError("MS_ENTRA_TENANT_ID must identify one tenant")
    if not all(character.isalnum() or character in ".-" for character in tenant_id):
        raise ConfigurationError("MS_ENTRA_TENANT_ID contains unsupported characters")
    return tenant_id


def _default_authority(tenant_id: str) -> str:
    return f"https://{_DEFAULT_AUTHORITY_HOST}/{tenant_id}"


def _validate_authority(authority: str, tenant_id: str) -> str:
    try:
        parsed = urlsplit(authority)
    except ValueError:
        raise ConfigurationError("MS_ENTRA_AUTHORITY must be an absolute HTTPS URL") from None
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not _has_valid_port(parsed)
    ):
        raise ConfigurationError("MS_ENTRA_AUTHORITY must be an absolute HTTPS URL")

    authority_tenant = parsed.path.strip("/")
    if not authority_tenant or "/" in authority_tenant:
        raise ConfigurationError("MS_ENTRA_AUTHORITY must contain exactly one tenant path")
    if authority_tenant.casefold() != tenant_id.casefold():
        raise ConfigurationError("MS_ENTRA_AUTHORITY tenant must match MS_ENTRA_TENANT_ID")

    return authority.rstrip("/")


def _validate_redirect_uri(redirect_uri: str) -> str:
    try:
        parsed = urlsplit(redirect_uri)
    except ValueError as exc:
        raise ConfigurationError("MS_ENTRA_REDIRECT_URI must be an absolute HTTP(S) URL") from exc
    if (
        parsed.scheme.casefold() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or not _has_valid_port(parsed)
    ):
        raise ConfigurationError("MS_ENTRA_REDIRECT_URI must be an absolute HTTP(S) URL")

    if parsed.scheme.casefold() == "http" and not _is_loopback_host(parsed.hostname):
        raise ConfigurationError(
            "MS_ENTRA_REDIRECT_URI must use HTTPS outside loopback development"
        )
    return redirect_uri


def _has_valid_port(parsed: SplitResult) -> bool:
    try:
        _ = parsed.port
    except ValueError:
        return False
    return True


def _is_loopback_host(host: str) -> bool:
    if host.casefold() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _validate_scopes(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ConfigurationError("MS_ENTRA_SCOPES must be a non-string iterable")

    normalized: list[str] = []
    seen: set[str] = set()
    for scope in value:
        if not isinstance(scope, str):
            raise ConfigurationError("MS_ENTRA_SCOPES entries must be strings")
        clean_scope = scope.strip()
        if not clean_scope or _is_placeholder(clean_scope):
            raise ConfigurationError("MS_ENTRA_SCOPES entries must contain real values")
        if clean_scope not in seen:
            normalized.append(clean_scope)
            seen.add(clean_scope)

    if not normalized:
        raise ConfigurationError("MS_ENTRA_SCOPES must contain at least one scope")
    return tuple(normalized)
