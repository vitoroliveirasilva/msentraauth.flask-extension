from __future__ import annotations

from ipaddress import ip_address
from urllib.parse import SplitResult, urlsplit

from ..config import MicrosoftEntraAuthConfig
from ..errors import InvalidNavigationTarget

_MAX_NEXT_URL_LENGTH = 2_048


def validate_next_url(value: object | None, config: MicrosoftEntraAuthConfig) -> str:
    # Retorna um destino de navegação local ou permitido com segurança
    if value is None:
        return config.post_login_redirect_uri
    if not isinstance(value, str):
        raise InvalidNavigationTarget("navigation target must be a string")

    candidate = value.strip()
    if (
        not candidate
        or len(candidate) > _MAX_NEXT_URL_LENGTH
        or "\\" in candidate
        or any(ord(character) < 32 for character in candidate)
    ):
        raise InvalidNavigationTarget("navigation target is invalid")

    try:
        parsed = urlsplit(candidate)
    except ValueError:
        raise InvalidNavigationTarget("navigation target is invalid") from None

    if parsed.fragment:
        raise InvalidNavigationTarget("navigation target must not contain a fragment")

    if not parsed.scheme and not parsed.netloc:
        if not candidate.startswith("/") or candidate.startswith("//"):
            raise InvalidNavigationTarget("navigation target must be a local absolute path")
        return candidate

    if (
        parsed.scheme.casefold() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or not _has_valid_port(parsed)
        or parsed.netloc.casefold() not in config.allowed_next_hosts
    ):
        raise InvalidNavigationTarget("navigation target host is not allowed")
    if parsed.scheme.casefold() == "http" and not _is_loopback_host(parsed.hostname):
        raise InvalidNavigationTarget("navigation target must use HTTPS")
    return candidate


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
