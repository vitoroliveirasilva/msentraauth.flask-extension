from collections.abc import Iterator

import pytest
from flask import Flask

from flask_ms_entra_auth import ConfigurationError, MicrosoftEntraAuth

_VALID_CONFIG: dict[str, object] = {
    "MS_ENTRA_CLIENT_ID": "11111111-1111-1111-1111-111111111111",
    "MS_ENTRA_CLIENT_SECRET": "safe-test-secret",
    "MS_ENTRA_TENANT_ID": "contoso.onmicrosoft.com",
    "MS_ENTRA_REDIRECT_URI": "https://app.example.com/auth/callback",
}


def create_app(name: str = "config-test", **overrides: object) -> Flask:
    app = Flask(name)
    app.config.from_mapping(_VALID_CONFIG)
    app.config.update(overrides)
    return app


@pytest.mark.parametrize(
    "key",
    [
        "MS_ENTRA_CLIENT_ID",
        "MS_ENTRA_CLIENT_SECRET",
        "MS_ENTRA_TENANT_ID",
        "MS_ENTRA_REDIRECT_URI",
    ],
)
def test_missing_required_configuration_is_rejected(key: str) -> None:
    app = create_app()
    app.config.pop(key)

    with pytest.raises(ConfigurationError, match=key):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("value", [None, 123, object()])
def test_required_configuration_must_be_text(value: object) -> None:
    app = create_app(MS_ENTRA_CLIENT_ID=value)

    with pytest.raises(ConfigurationError, match="MS_ENTRA_CLIENT_ID"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    "value",
    ["", "   ", "...", "CHANGE-ME", "<client-id>", "{{ CLIENT_ID }}"],
)
def test_blank_or_placeholder_configuration_is_rejected(value: str) -> None:
    app = create_app(MS_ENTRA_CLIENT_ID=value)

    with pytest.raises(ConfigurationError, match="real value"):
        MicrosoftEntraAuth().init_app(app)


def test_sensitive_value_is_not_exposed_in_configuration_error() -> None:
    secret = "<client-secret>"
    app = create_app(MS_ENTRA_CLIENT_SECRET=secret)

    with pytest.raises(ConfigurationError) as raised:
        MicrosoftEntraAuth().init_app(app)

    assert secret not in str(raised.value)


@pytest.mark.parametrize("tenant", ["common", "organizations", "CONSUMERS"])
def test_reserved_multitenant_alias_is_rejected(tenant: str) -> None:
    app = create_app(MS_ENTRA_TENANT_ID=tenant)

    with pytest.raises(ConfigurationError, match="one tenant"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("tenant", ["tenant/path", "tenant name", "tenant_underscore"])
def test_tenant_with_unsupported_characters_is_rejected(tenant: str) -> None:
    app = create_app(MS_ENTRA_TENANT_ID=tenant)

    with pytest.raises(ConfigurationError, match="unsupported characters"):
        MicrosoftEntraAuth().init_app(app)


def test_default_authority_and_scopes_are_derived_safely() -> None:
    app = create_app()

    MicrosoftEntraAuth().init_app(app)

    config = app.extensions["ms_entra_auth"].config
    assert config.authority == "https://login.microsoftonline.com/contoso.onmicrosoft.com"
    assert config.scopes == ("User.Read",)


def test_custom_authority_is_accepted_and_trailing_slash_is_removed() -> None:
    app = create_app(MS_ENTRA_AUTHORITY="https://login.microsoftonline.us/contoso.onmicrosoft.com/")

    MicrosoftEntraAuth().init_app(app)

    assert app.extensions["ms_entra_auth"].config.authority == (
        "https://login.microsoftonline.us/contoso.onmicrosoft.com"
    )


@pytest.mark.parametrize(
    "authority",
    [
        "http://login.example.com/contoso.onmicrosoft.com",
        "relative/contoso.onmicrosoft.com",
        "https://user:password@login.example.com/contoso.onmicrosoft.com",
        "https://login.example.com/contoso.onmicrosoft.com?query=yes",
        "https://login.example.com/contoso.onmicrosoft.com#fragment",
        "https://login.example.com:invalid/contoso.onmicrosoft.com",
        "https://[invalid/contoso.onmicrosoft.com",
    ],
)
def test_authority_must_be_absolute_safe_https_url(authority: str) -> None:
    app = create_app(MS_ENTRA_AUTHORITY=authority)

    with pytest.raises(ConfigurationError, match="absolute HTTPS"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    "authority",
    [
        "https://login.example.com",
        "https://login.example.com/tenant/extra",
    ],
)
def test_authority_must_have_exactly_one_tenant_path(authority: str) -> None:
    app = create_app(MS_ENTRA_AUTHORITY=authority)

    with pytest.raises(ConfigurationError, match="exactly one tenant path"):
        MicrosoftEntraAuth().init_app(app)


def test_authority_tenant_must_match_configured_tenant() -> None:
    app = create_app(MS_ENTRA_AUTHORITY="https://login.example.com/other.example.com")

    with pytest.raises(ConfigurationError, match="must match"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "/auth/callback",
        "ftp://app.example.com/auth/callback",
        "https://user:password@app.example.com/auth/callback",
        "https://app.example.com/auth/callback#fragment",
        "https://app.example.com:invalid/auth/callback",
        "https://[invalid/auth/callback",
    ],
)
def test_redirect_uri_must_be_absolute_http_url(redirect_uri: str) -> None:
    app = create_app(MS_ENTRA_REDIRECT_URI=redirect_uri)

    with pytest.raises(ConfigurationError, match=r"absolute HTTP\(S\)"):
        MicrosoftEntraAuth().init_app(app)


def test_http_redirect_is_rejected_outside_loopback() -> None:
    app = create_app(MS_ENTRA_REDIRECT_URI="http://app.example.com/auth/callback")

    with pytest.raises(ConfigurationError, match="HTTPS outside loopback"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "http://localhost/auth/callback",
        "http://127.0.0.1:5000/auth/callback",
        "http://[::1]:5000/auth/callback",
        "https://app.example.com/auth/callback?source=entra",
    ],
)
def test_https_and_loopback_development_redirects_are_accepted(redirect_uri: str) -> None:
    app = create_app(MS_ENTRA_REDIRECT_URI=redirect_uri)

    MicrosoftEntraAuth().init_app(app)

    assert app.extensions["ms_entra_auth"].config.redirect_uri == redirect_uri


def test_hostname_that_is_not_an_ip_is_not_treated_as_loopback() -> None:
    app = create_app(MS_ENTRA_REDIRECT_URI="http://localhost.example.com/callback")

    with pytest.raises(ConfigurationError, match="HTTPS outside loopback"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("scopes", ["User.Read", 123, object()])
def test_scopes_must_be_non_string_iterable(scopes: object) -> None:
    app = create_app(MS_ENTRA_SCOPES=scopes)

    with pytest.raises(ConfigurationError, match="non-string iterable"):
        MicrosoftEntraAuth().init_app(app)


def test_constructor_scope_string_is_rejected_instead_of_split_into_characters() -> None:
    app = create_app()

    with pytest.raises(ConfigurationError, match="non-string iterable"):
        MicrosoftEntraAuth(scopes="User.Read").init_app(app)


@pytest.mark.parametrize("scopes", [[123], ["User.Read", object()]])
def test_scope_entries_must_be_strings(scopes: list[object]) -> None:
    app = create_app(MS_ENTRA_SCOPES=scopes)

    with pytest.raises(ConfigurationError, match="entries must be strings"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("scopes", [[], [""], ["   "], ["..."]])
def test_scopes_must_contain_real_values(scopes: list[str]) -> None:
    app = create_app(MS_ENTRA_SCOPES=scopes)
    expected = "at least one" if not scopes else "real values"

    with pytest.raises(ConfigurationError, match=expected):
        MicrosoftEntraAuth().init_app(app)


def test_scopes_are_trimmed_deduplicated_and_detached_from_app_config() -> None:
    scopes = [" User.Read ", "User.Read", "Mail.Read"]
    app = create_app(MS_ENTRA_SCOPES=scopes)

    MicrosoftEntraAuth().init_app(app)
    scopes.append("Files.Read")

    assert app.extensions["ms_entra_auth"].config.scopes == ("User.Read", "Mail.Read")


def test_scope_generator_is_materialized_for_reuse_across_apps() -> None:
    def generate_scopes() -> Iterator[str]:
        yield "User.Read"
        yield "Mail.Read"

    extension = MicrosoftEntraAuth(scopes=generate_scopes())
    first_app = create_app()
    second_app = create_app()

    extension.init_app(first_app)
    extension.init_app(second_app)

    assert first_app.extensions["ms_entra_auth"].config.scopes == ("User.Read", "Mail.Read")
    assert second_app.extensions["ms_entra_auth"].config.scopes == ("User.Read", "Mail.Read")


def test_default_session_namespace_is_stable_and_application_specific() -> None:
    first = create_app("namespace-first")
    second = create_app("namespace-second")

    MicrosoftEntraAuth().init_app(first)
    MicrosoftEntraAuth().init_app(second)

    first_namespace = first.extensions["ms_entra_auth"].config.session_namespace
    second_namespace = second.extensions["ms_entra_auth"].config.session_namespace
    assert first_namespace.startswith("app-")
    assert len(first_namespace) == 28
    assert first_namespace != second_namespace

    repeated = create_app("namespace-first")
    MicrosoftEntraAuth().init_app(repeated)
    assert repeated.extensions["ms_entra_auth"].config.session_namespace == first_namespace


def test_explicit_session_namespace_is_normalized_from_app_config() -> None:
    app = create_app("namespace-explicit")
    app.config["MS_ENTRA_SESSION_NAMESPACE"] = "  app.production_01  "

    MicrosoftEntraAuth().init_app(app)

    assert app.extensions["ms_entra_auth"].config.session_namespace == "app.production_01"


@pytest.mark.parametrize(
    "namespace",
    ["has space", "has:colon", "unsafe/segment", "x" * 129],
)
def test_invalid_session_namespace_is_rejected(namespace: str) -> None:
    app = create_app("namespace-invalid")
    app.config["MS_ENTRA_SESSION_NAMESPACE"] = namespace

    with pytest.raises(ConfigurationError, match="MS_ENTRA_SESSION_NAMESPACE"):
        MicrosoftEntraAuth().init_app(app)


def test_token_cache_ttl_defaults_to_eight_hours() -> None:
    app = create_app()

    MicrosoftEntraAuth().init_app(app)

    assert app.extensions["ms_entra_auth"].config.token_cache_ttl == 28_800


def test_token_cache_ttl_can_be_configured_and_constructor_wins() -> None:
    app = create_app(MS_ENTRA_TOKEN_CACHE_TTL=3600)

    MicrosoftEntraAuth(token_cache_ttl=7200).init_app(app)

    assert app.extensions["ms_entra_auth"].config.token_cache_ttl == 7200


@pytest.mark.parametrize("ttl", [True, False, 0, -1, 1.5, "3600", object()])
def test_token_cache_ttl_must_be_positive_integer(ttl: object) -> None:
    app = create_app(MS_ENTRA_TOKEN_CACHE_TTL=ttl)

    with pytest.raises(ConfigurationError, match="MS_ENTRA_TOKEN_CACHE_TTL"):
        MicrosoftEntraAuth().init_app(app)


def test_web_configuration_defaults_are_safe() -> None:
    app = create_app()

    MicrosoftEntraAuth().init_app(app)

    config = app.extensions["ms_entra_auth"].config
    assert config.flow_ttl == 600
    assert config.identity_ttl == 28_800
    assert config.url_prefix == "/auth"
    assert config.post_login_redirect_uri == "/"
    assert config.post_logout_redirect_uri == "/"
    assert config.allowed_next_hosts == ()
    assert config.auto_register_routes is True
    assert config.handle_route_errors is True
    assert config.unauthenticated_mode == "redirect"


def test_web_configuration_constructor_values_take_precedence() -> None:
    app = create_app(
        MS_ENTRA_FLOW_TTL=10,
        MS_ENTRA_IDENTITY_TTL=20,
        MS_ENTRA_URL_PREFIX="/from-app",
        MS_ENTRA_ALLOWED_NEXT_HOSTS=["app.example.com"],
        MS_ENTRA_POST_LOGIN_REDIRECT_URI="/from-app-login",
        MS_ENTRA_POST_LOGOUT_REDIRECT_URI="/from-app-logout",
        MS_ENTRA_AUTO_REGISTER_ROUTES=True,
        MS_ENTRA_HANDLE_ROUTE_ERRORS=True,
        MS_ENTRA_UNAUTHENTICATED_MODE="redirect",
    )
    hosts = ["EXAMPLE.COM:443", "example.com:443", "localhost:5000"]
    extension = MicrosoftEntraAuth(
        flow_ttl=30,
        identity_ttl=40,
        url_prefix="/custom/",
        allowed_next_hosts=hosts,
        post_login_redirect_uri="https://example.com:443/after-login",
        post_logout_redirect_uri="http://localhost:5000/after-logout",
        auto_register_routes=False,
        handle_route_errors=False,
        unauthenticated_mode="RAISE",
    )
    hosts.append("later.example.com")

    extension.init_app(app)

    config = app.extensions["ms_entra_auth"].config
    assert config.flow_ttl == 30
    assert config.identity_ttl == 40
    assert config.url_prefix == "/custom"
    assert config.allowed_next_hosts == ("example.com:443", "localhost:5000")
    assert config.post_login_redirect_uri == "https://example.com:443/after-login"
    assert config.post_logout_redirect_uri == "http://localhost:5000/after-logout"
    assert config.auto_register_routes is False
    assert config.handle_route_errors is False
    assert config.unauthenticated_mode == "raise"


@pytest.mark.parametrize("key", ["MS_ENTRA_FLOW_TTL", "MS_ENTRA_IDENTITY_TTL"])
@pytest.mark.parametrize("value", [True, 0, -1, "600", 1.5])
def test_web_ttls_must_be_positive_integers(key: str, value: object) -> None:
    app = create_app()
    app.config[key] = value

    with pytest.raises(ConfigurationError, match=key):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    "prefix",
    ["auth", "//auth", "/auth?x=1", "/auth#x", "/auth\\callback", "/"],
)
def test_url_prefix_must_be_safe_local_non_root_path(prefix: str) -> None:
    app = create_app(MS_ENTRA_URL_PREFIX=prefix)

    with pytest.raises(ConfigurationError, match="MS_ENTRA_URL_PREFIX"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("value", ["example.com", 123, object()])
def test_allowed_next_hosts_must_be_non_string_iterable(value: object) -> None:
    app = create_app(MS_ENTRA_ALLOWED_NEXT_HOSTS=value)

    with pytest.raises(ConfigurationError, match="MS_ENTRA_ALLOWED_NEXT_HOSTS"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    "host",
    ["", "https://example.com", "user@example.com", "example.com/path", "[invalid", "x:bad"],
)
def test_allowed_next_host_entries_must_be_plain_hosts(host: str) -> None:
    app = create_app(MS_ENTRA_ALLOWED_NEXT_HOSTS=[host])

    with pytest.raises(ConfigurationError, match="MS_ENTRA_ALLOWED_NEXT_HOSTS"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize(
    ("key", "value", "match"),
    [
        ("MS_ENTRA_POST_LOGIN_REDIRECT_URI", "relative", "safe local path"),
        ("MS_ENTRA_POST_LOGIN_REDIRECT_URI", "//evil.example.com", "allowed host"),
        ("MS_ENTRA_POST_LOGOUT_REDIRECT_URI", "/safe#fragment", "safe local path"),
        ("MS_ENTRA_POST_LOGOUT_REDIRECT_URI", "/safe\\path", "safe local path"),
        ("MS_ENTRA_POST_LOGIN_REDIRECT_URI", "https://evil.example.com/x", "allowed host"),
        ("MS_ENTRA_POST_LOGIN_REDIRECT_URI", "http://example.com/x", "allowed host"),
        ("MS_ENTRA_POST_LOGIN_REDIRECT_URI", "https://[invalid", "safe redirect URI"),
    ],
)
def test_configured_navigation_targets_are_validated(key: str, value: str, match: str) -> None:
    app = create_app(**{key: value})

    with pytest.raises(ConfigurationError, match=match):
        MicrosoftEntraAuth().init_app(app)


def test_external_navigation_target_requires_https_outside_loopback() -> None:
    app = create_app(
        MS_ENTRA_ALLOWED_NEXT_HOSTS=["example.com"],
        MS_ENTRA_POST_LOGIN_REDIRECT_URI="http://example.com/after",
    )

    with pytest.raises(ConfigurationError, match="HTTPS outside loopback"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("key", ["MS_ENTRA_AUTO_REGISTER_ROUTES", "MS_ENTRA_HANDLE_ROUTE_ERRORS"])
@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_web_flags_must_be_booleans(key: str, value: object) -> None:
    app = create_app()
    app.config[key] = value

    if value is None:
        MicrosoftEntraAuth().init_app(app)
        return
    with pytest.raises(ConfigurationError, match=key):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("value", [123, "", "unknown", "redirect-now"])
def test_unauthenticated_mode_is_validated(value: object) -> None:
    app = create_app(MS_ENTRA_UNAUTHENTICATED_MODE=value)

    with pytest.raises(ConfigurationError, match="MS_ENTRA_UNAUTHENTICATED_MODE"):
        MicrosoftEntraAuth().init_app(app)


@pytest.mark.parametrize("value", ["X Header", "X_Header", "x" * 129])
def test_request_id_header_rejects_unsafe_values(value: str) -> None:
    app = create_app()
    app.config["MS_ENTRA_REQUEST_ID_HEADER"] = value

    with pytest.raises(ConfigurationError, match="REQUEST_ID_HEADER"):
        MicrosoftEntraAuth().init_app(app)


def test_hardening_configuration_is_resolved_and_constructor_overrides_win() -> None:
    app = create_app()
    app.config.update(
        MS_ENTRA_EVENT_LOGGING=False,
        MS_ENTRA_REQUEST_ID_HEADER="X-App-Request-ID",
        MS_ENTRA_REQUIRE_ATOMIC_STORAGE=False,
        MS_ENTRA_STRICT_SECURITY=False,
    )
    extension = MicrosoftEntraAuth(
        event_logging=True,
        request_id_header="X-Override-ID",
        require_atomic_storage=True,
        strict_security=True,
    )
    app.secret_key = "x" * 32
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=True,
    )
    extension.init_app(app)

    resolved = app.extensions["ms_entra_auth"].config
    assert resolved.event_logging is True
    assert resolved.request_id_header == "X-Override-ID"
    assert resolved.require_atomic_storage is True
    assert resolved.strict_security is True
