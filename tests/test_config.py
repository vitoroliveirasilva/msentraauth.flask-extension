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


def create_app(**overrides: object) -> Flask:
    app = Flask("config-test")
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
def test_https_and_loopback_development_redirects_are_accepted(
    redirect_uri: str,
) -> None:
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

    assert first_app.extensions["ms_entra_auth"].config.scopes == (
        "User.Read",
        "Mail.Read",
    )
    assert second_app.extensions["ms_entra_auth"].config.scopes == (
        "User.Read",
        "Mail.Read",
    )
