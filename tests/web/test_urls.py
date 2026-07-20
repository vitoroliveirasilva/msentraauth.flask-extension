from __future__ import annotations

import pytest

from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.errors import InvalidNavigationTarget
from flask_ms_entra_auth.web.urls import validate_next_url


def config(*, allowed_hosts: tuple[str, ...] = ()) -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client",
        client_secret="secret",
        tenant_id="tenant",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant",
        scopes=("User.Read",),
        session_namespace="app",
        token_cache_ttl=3600,
        post_login_redirect_uri="/default",
        allowed_next_hosts=allowed_hosts,
    )


def test_none_uses_configured_default() -> None:
    assert validate_next_url(None, config()) == "/default"


@pytest.mark.parametrize("value", [123, object()])
def test_navigation_target_must_be_text(value: object) -> None:
    with pytest.raises(InvalidNavigationTarget, match="string"):
        validate_next_url(value, config())


@pytest.mark.parametrize(
    "value",
    ["", "   ", "/bad\\path", "/bad\npath", "/" + "x" * 2048],
)
def test_invalid_navigation_target_shape_is_rejected(value: str) -> None:
    with pytest.raises(InvalidNavigationTarget, match="invalid"):
        validate_next_url(value, config())


def test_malformed_url_is_rejected_without_raw_value() -> None:
    value = "https://[invalid"

    with pytest.raises(InvalidNavigationTarget) as raised:
        validate_next_url(value, config())

    assert value not in str(raised.value)


def test_fragment_is_rejected() -> None:
    with pytest.raises(InvalidNavigationTarget, match="fragment"):
        validate_next_url("/dashboard#private", config())


def test_relative_target_must_be_absolute_path() -> None:
    with pytest.raises(InvalidNavigationTarget, match="local absolute path"):
        validate_next_url("dashboard", config())


def test_scheme_relative_target_is_treated_as_external_and_rejected() -> None:
    with pytest.raises(InvalidNavigationTarget, match="host is not allowed"):
        validate_next_url("//evil.example.com/path", config())


def test_local_path_and_query_are_preserved() -> None:
    assert validate_next_url(" /dashboard?tab=1 ", config()) == "/dashboard?tab=1"


@pytest.mark.parametrize(
    "value",
    [
        "ftp://example.com/path",
        "https:///missing-host",
        "https://user@example.com/path",
        "https://user:pass@example.com/path",
        "https://example.com:bad/path",
        "https://other.example.com/path",
    ],
)
def test_external_target_requires_safe_allowlisted_host(value: str) -> None:
    with pytest.raises(InvalidNavigationTarget, match="host is not allowed"):
        validate_next_url(value, config(allowed_hosts=("example.com",)))


def test_http_external_target_is_rejected_even_when_host_is_allowed() -> None:
    with pytest.raises(InvalidNavigationTarget, match="HTTPS"):
        validate_next_url("http://example.com/path", config(allowed_hosts=("example.com",)))


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/path?x=1",
        "http://localhost:5000/path",
        "http://127.0.0.1:5000/path",
        "http://[::1]:5000/path",
    ],
)
def test_allowed_https_and_loopback_targets_are_preserved(value: str) -> None:
    host = value.split("//", 1)[1].split("/", 1)[0].casefold()
    assert validate_next_url(value, config(allowed_hosts=(host,))) == value


def test_non_ip_hostname_is_not_treated_as_loopback() -> None:
    with pytest.raises(InvalidNavigationTarget, match="HTTPS"):
        validate_next_url(
            "http://localhost.example.com/path",
            config(allowed_hosts=("localhost.example.com",)),
        )
