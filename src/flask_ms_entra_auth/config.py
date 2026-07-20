from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from ipaddress import ip_address
from typing import Final
from urllib.parse import SplitResult, urlsplit

from .errors import ConfigurationError

_DEFAULT_AUTHORITY_HOST: Final = "login.microsoftonline.com"
_DEFAULT_SCOPES: Final = ("User.Read",)
_DEFAULT_TOKEN_CACHE_TTL: Final = 28_800
_DEFAULT_FLOW_TTL: Final = 600
_DEFAULT_IDENTITY_TTL: Final = 28_800
_DEFAULT_URL_PREFIX: Final = "/auth"
_DEFAULT_POST_LOGIN_REDIRECT_URI: Final = "/"
_DEFAULT_POST_LOGOUT_REDIRECT_URI: Final = "/"
_DEFAULT_UNAUTHENTICATED_MODE: Final = "redirect"
_DEFAULT_REQUEST_ID_HEADER: Final = "X-Request-ID"
_UNAUTHENTICATED_MODES: Final = frozenset({"raise", "redirect"})
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
    # Validada e imutável configuração de autenticação do Microsoft Entra, pertencente a uma aplicação Flask

    client_id: str
    client_secret: str = field(repr=False)
    tenant_id: str
    redirect_uri: str
    authority: str
    scopes: tuple[str, ...]
    session_namespace: str
    token_cache_ttl: int
    flow_ttl: int = _DEFAULT_FLOW_TTL
    identity_ttl: int = _DEFAULT_IDENTITY_TTL
    url_prefix: str = _DEFAULT_URL_PREFIX
    post_login_redirect_uri: str = _DEFAULT_POST_LOGIN_REDIRECT_URI
    post_logout_redirect_uri: str = _DEFAULT_POST_LOGOUT_REDIRECT_URI
    allowed_next_hosts: tuple[str, ...] = ()
    auto_register_routes: bool = True
    handle_route_errors: bool = True
    unauthenticated_mode: str = _DEFAULT_UNAUTHENTICATED_MODE
    event_logging: bool = False
    request_id_header: str = _DEFAULT_REQUEST_ID_HEADER
    require_atomic_storage: bool = False
    strict_security: bool = False


@dataclass(frozen=True, slots=True)
class ConfigOverrides:
    # Imutabilidade de valores no nível do construtor com precedência sobre ``app.config``

    client_id: str | None = None
    client_secret: str | None = None
    tenant_id: str | None = None
    redirect_uri: str | None = None
    authority: str | None = None
    scopes: Iterable[str] | None = None
    session_namespace: str | None = None
    token_cache_ttl: int | None = None
    flow_ttl: int | None = None
    identity_ttl: int | None = None
    url_prefix: str | None = None
    post_login_redirect_uri: str | None = None
    post_logout_redirect_uri: str | None = None
    allowed_next_hosts: Iterable[str] | None = None
    auto_register_routes: bool | None = None
    handle_route_errors: bool | None = None
    unauthenticated_mode: str | None = None
    event_logging: bool | None = None
    request_id_header: str | None = None
    require_atomic_storage: bool | None = None
    strict_security: bool | None = None


def resolve_config(
    app_config: Mapping[str, object],
    overrides: ConfigOverrides,
    *,
    app_name: str,
) -> MicrosoftEntraAuthConfig:
    # Resolve construtor overrides, Flask configuração e safe defaults
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

    namespace_value = _pick(overrides.session_namespace, app_config, "MS_ENTRA_SESSION_NAMESPACE")
    session_namespace = (
        _default_session_namespace(app_name, client_id, tenant_id)
        if namespace_value is None
        else _validate_session_namespace(
            _required_text("MS_ENTRA_SESSION_NAMESPACE", namespace_value)
        )
    )

    token_cache_ttl_value = _pick(
        overrides.token_cache_ttl,
        app_config,
        "MS_ENTRA_TOKEN_CACHE_TTL",
    )
    token_cache_ttl = _validate_positive_integer(
        "MS_ENTRA_TOKEN_CACHE_TTL",
        _DEFAULT_TOKEN_CACHE_TTL if token_cache_ttl_value is None else token_cache_ttl_value,
    )

    flow_ttl_value = _pick(overrides.flow_ttl, app_config, "MS_ENTRA_FLOW_TTL")
    flow_ttl = _validate_positive_integer(
        "MS_ENTRA_FLOW_TTL",
        _DEFAULT_FLOW_TTL if flow_ttl_value is None else flow_ttl_value,
    )

    identity_ttl_value = _pick(overrides.identity_ttl, app_config, "MS_ENTRA_IDENTITY_TTL")
    identity_ttl = _validate_positive_integer(
        "MS_ENTRA_IDENTITY_TTL",
        _DEFAULT_IDENTITY_TTL if identity_ttl_value is None else identity_ttl_value,
    )

    url_prefix_value = _pick(overrides.url_prefix, app_config, "MS_ENTRA_URL_PREFIX")
    url_prefix = _validate_url_prefix(
        _DEFAULT_URL_PREFIX
        if url_prefix_value is None
        else _required_text("MS_ENTRA_URL_PREFIX", url_prefix_value)
    )

    allowed_hosts_value = _pick(
        overrides.allowed_next_hosts,
        app_config,
        "MS_ENTRA_ALLOWED_NEXT_HOSTS",
    )
    allowed_next_hosts = _validate_allowed_next_hosts(
        () if allowed_hosts_value is None else allowed_hosts_value
    )

    post_login_value = _pick(
        overrides.post_login_redirect_uri,
        app_config,
        "MS_ENTRA_POST_LOGIN_REDIRECT_URI",
    )
    post_login_redirect_uri = _validate_configured_next_uri(
        "MS_ENTRA_POST_LOGIN_REDIRECT_URI",
        _DEFAULT_POST_LOGIN_REDIRECT_URI
        if post_login_value is None
        else _required_text("MS_ENTRA_POST_LOGIN_REDIRECT_URI", post_login_value),
        allowed_next_hosts,
    )

    post_logout_value = _pick(
        overrides.post_logout_redirect_uri,
        app_config,
        "MS_ENTRA_POST_LOGOUT_REDIRECT_URI",
    )
    post_logout_redirect_uri = _validate_configured_next_uri(
        "MS_ENTRA_POST_LOGOUT_REDIRECT_URI",
        _DEFAULT_POST_LOGOUT_REDIRECT_URI
        if post_logout_value is None
        else _required_text("MS_ENTRA_POST_LOGOUT_REDIRECT_URI", post_logout_value),
        allowed_next_hosts,
    )

    auto_register_value = _pick(
        overrides.auto_register_routes,
        app_config,
        "MS_ENTRA_AUTO_REGISTER_ROUTES",
    )
    auto_register_routes = _validate_boolean(
        "MS_ENTRA_AUTO_REGISTER_ROUTES",
        True if auto_register_value is None else auto_register_value,
    )

    handle_errors_value = _pick(
        overrides.handle_route_errors,
        app_config,
        "MS_ENTRA_HANDLE_ROUTE_ERRORS",
    )
    handle_route_errors = _validate_boolean(
        "MS_ENTRA_HANDLE_ROUTE_ERRORS",
        True if handle_errors_value is None else handle_errors_value,
    )

    unauthenticated_value = _pick(
        overrides.unauthenticated_mode,
        app_config,
        "MS_ENTRA_UNAUTHENTICATED_MODE",
    )
    unauthenticated_mode = _validate_unauthenticated_mode(
        _DEFAULT_UNAUTHENTICATED_MODE if unauthenticated_value is None else unauthenticated_value
    )

    event_logging_value = _pick(overrides.event_logging, app_config, "MS_ENTRA_EVENT_LOGGING")
    event_logging = _validate_boolean(
        "MS_ENTRA_EVENT_LOGGING",
        False if event_logging_value is None else event_logging_value,
    )

    request_id_header_value = _pick(
        overrides.request_id_header,
        app_config,
        "MS_ENTRA_REQUEST_ID_HEADER",
    )
    request_id_header = _validate_request_id_header(
        _DEFAULT_REQUEST_ID_HEADER
        if request_id_header_value is None
        else _required_text("MS_ENTRA_REQUEST_ID_HEADER", request_id_header_value)
    )

    require_atomic_value = _pick(
        overrides.require_atomic_storage,
        app_config,
        "MS_ENTRA_REQUIRE_ATOMIC_STORAGE",
    )
    require_atomic_storage = _validate_boolean(
        "MS_ENTRA_REQUIRE_ATOMIC_STORAGE",
        False if require_atomic_value is None else require_atomic_value,
    )

    strict_security_value = _pick(
        overrides.strict_security,
        app_config,
        "MS_ENTRA_STRICT_SECURITY",
    )
    strict_security = _validate_boolean(
        "MS_ENTRA_STRICT_SECURITY",
        False if strict_security_value is None else strict_security_value,
    )

    return MicrosoftEntraAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
        redirect_uri=redirect_uri,
        authority=authority,
        scopes=scopes,
        session_namespace=session_namespace,
        token_cache_ttl=token_cache_ttl,
        flow_ttl=flow_ttl,
        identity_ttl=identity_ttl,
        url_prefix=url_prefix,
        post_login_redirect_uri=post_login_redirect_uri,
        post_logout_redirect_uri=post_logout_redirect_uri,
        allowed_next_hosts=allowed_next_hosts,
        auto_register_routes=auto_register_routes,
        handle_route_errors=handle_route_errors,
        unauthenticated_mode=unauthenticated_mode,
        event_logging=event_logging,
        request_id_header=request_id_header,
        require_atomic_storage=require_atomic_storage,
        strict_security=strict_security,
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


def _default_session_namespace(app_name: str, client_id: str, tenant_id: str) -> str:
    payload = f"{app_name}\0{client_id}\0{tenant_id}".encode()
    digest = sha256(payload).hexdigest()[:24]
    return f"app-{digest}"


def _validate_session_namespace(namespace: str) -> str:
    if len(namespace) > 128 or any(
        not (character.isalnum() or character in "._-") for character in namespace
    ):
        raise ConfigurationError(
            "MS_ENTRA_SESSION_NAMESPACE must contain only letters, numbers, '.', '_' or '-'"
        )
    return namespace


def _validate_positive_integer(key: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"{key} must be a positive integer")
    return value


def _validate_boolean(key: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{key} must be a boolean")
    return value


def _validate_url_prefix(value: str) -> str:
    if (
        not value.startswith("/")
        or value.startswith("//")
        or "?" in value
        or "#" in value
        or "\\" in value
    ):
        raise ConfigurationError("MS_ENTRA_URL_PREFIX must be an absolute local path")
    normalized = value.rstrip("/")
    if not normalized:
        raise ConfigurationError("MS_ENTRA_URL_PREFIX must not target the application root")
    return normalized


def _validate_allowed_next_hosts(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ConfigurationError("MS_ENTRA_ALLOWED_NEXT_HOSTS must be a non-string iterable")

    normalized: list[str] = []
    seen: set[str] = set()
    for host in value:
        if not isinstance(host, str) or not host.strip():
            raise ConfigurationError("MS_ENTRA_ALLOWED_NEXT_HOSTS entries must be strings")
        clean_host = host.strip().casefold()
        try:
            parsed = urlsplit(f"//{clean_host}")
        except ValueError:
            raise ConfigurationError(
                "MS_ENTRA_ALLOWED_NEXT_HOSTS entries must be host names"
            ) from None
        if (
            not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not _has_valid_port(parsed)
            or clean_host != parsed.netloc.casefold()
        ):
            raise ConfigurationError("MS_ENTRA_ALLOWED_NEXT_HOSTS entries must be host names")
        if clean_host not in seen:
            normalized.append(clean_host)
            seen.add(clean_host)
    return tuple(normalized)


def _validate_configured_next_uri(
    key: str,
    value: str,
    allowed_hosts: tuple[str, ...],
) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise ConfigurationError(f"{key} must be a safe redirect URI") from None

    if parsed.scheme or parsed.netloc:
        if (
            parsed.scheme.casefold() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or not _has_valid_port(parsed)
            or parsed.netloc.casefold() not in allowed_hosts
        ):
            raise ConfigurationError(f"{key} must use an explicitly allowed host")
        if parsed.scheme.casefold() == "http" and not _is_loopback_host(parsed.hostname):
            raise ConfigurationError(f"{key} must use HTTPS outside loopback development")
        return value

    if not value.startswith("/") or value.startswith("//") or "\\" in value or parsed.fragment:
        raise ConfigurationError(f"{key} must be a safe local path")
    return value


def _validate_unauthenticated_mode(value: object) -> str:
    if not isinstance(value, str):
        raise ConfigurationError("MS_ENTRA_UNAUTHENTICATED_MODE must be 'redirect' or 'raise'")
    normalized = value.strip().casefold()
    if normalized not in _UNAUTHENTICATED_MODES:
        raise ConfigurationError("MS_ENTRA_UNAUTHENTICATED_MODE must be 'redirect' or 'raise'")
    return normalized


def _validate_request_id_header(value: str) -> str:
    if len(value) > 128 or any(
        not (character.isalnum() or character == "-") for character in value
    ):
        raise ConfigurationError(
            "MS_ENTRA_REQUEST_ID_HEADER must contain only letters, numbers, or '-'"
        )
    return value
