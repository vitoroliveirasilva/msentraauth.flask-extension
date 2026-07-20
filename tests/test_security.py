from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from flask import Flask

from flask_ms_entra_auth import ConfigurationError, MemoryStorage, MicrosoftEntraAuth
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.security import SecurityFinding, audit_security
from flask_ms_entra_auth.storage.namespaced import NamespacedStorage


class BasicStorage:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def load(self, key: str) -> bytes | None:
        return self.values.get(key)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del ttl
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


def config(
    redirect_uri: str = "https://app.example.com/auth/callback",
) -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="secret",
        tenant_id="tenant-id",
        redirect_uri=redirect_uri,
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="security",
        token_cache_ttl=100,
    )


def secure_app() -> Flask:
    app = Flask("security-test")
    app.testing = True
    app.secret_key = "x" * 32
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=True,
    )
    return app


def finding_codes(app: Flask, *, backend: object, redirect_uri: str | None = None) -> set[str]:
    report = audit_security(
        app,
        config(redirect_uri or "https://app.example.com/auth/callback"),
        NamespacedStorage(backend, "security"),  # type: ignore[arg-type]
    )
    return {finding.code for finding in report.findings}


def test_hardened_report_has_no_findings_and_is_immutable() -> None:
    app = secure_app()
    report = audit_security(app, config(), NamespacedStorage(MemoryStorage(), "security"))

    assert report.findings == ()
    assert report.passed is True
    assert report.hardened is True
    with pytest.raises(FrozenInstanceError):
        report.findings = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        SecurityFinding("code", "info", "message").code = "changed"  # type: ignore[misc]


def test_audit_reports_missing_and_weak_flask_session_settings() -> None:
    app = Flask("weak-security")
    app.testing = False
    app.debug = False
    app.config.update(
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SAMESITE=None,
        SESSION_COOKIE_SECURE=False,
    )

    report = audit_security(app, config(), NamespacedStorage(MemoryStorage(), "security"))
    codes = {finding.code for finding in report.findings}

    assert codes == {
        "secret-key-missing",
        "session-cookie-httponly-disabled",
        "session-cookie-samesite-weak",
        "session-cookie-secure-disabled",
        "memory-storage-production",
    }
    assert report.passed is False
    assert report.hardened is False
    assert all(
        "secret" not in finding.message.casefold() or finding.code.startswith("secret")
        for finding in report.findings
    )


def test_audit_warns_for_short_bytes_secret_and_non_atomic_backend() -> None:
    app = secure_app()
    app.secret_key = b"short"
    app.testing = False
    codes = finding_codes(app, backend=BasicStorage())

    assert codes == {"secret-key-short", "atomic-consume-unavailable"}


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "http://localhost/auth/callback",
        "http://127.0.0.1/auth/callback",
        "http://[::1]/auth/callback",
    ],
)
def test_loopback_redirect_does_not_require_secure_cookie(redirect_uri: str) -> None:
    app = secure_app()
    app.config["SESSION_COOKIE_SECURE"] = False

    assert "session-cookie-secure-disabled" not in finding_codes(
        app,
        backend=MemoryStorage(),
        redirect_uri=redirect_uri,
    )


def test_non_loopback_or_unparseable_redirect_requires_secure_cookie() -> None:
    app = secure_app()
    app.config["SESSION_COOKIE_SECURE"] = False

    assert "session-cookie-secure-disabled" in finding_codes(
        app,
        backend=MemoryStorage(),
        redirect_uri="https://app.example.com/auth/callback",
    )
    assert "session-cookie-secure-disabled" in finding_codes(
        app,
        backend=MemoryStorage(),
        redirect_uri="relative-path",
    )


def configured_app(*, secret_key: str | None = "x" * 32) -> Flask:
    app = Flask("strict-security")
    app.testing = True
    app.secret_key = secret_key
    app.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="client-secret",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE="strict-security",
        MS_ENTRA_AUTO_REGISTER_ROUTES=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=True,
    )
    return app


def test_require_atomic_storage_rejects_backend_without_native_take() -> None:
    app = configured_app()
    app.config["MS_ENTRA_REQUIRE_ATOMIC_STORAGE"] = True

    with pytest.raises(ConfigurationError, match="atomic one-time"):
        MicrosoftEntraAuth(storage=BasicStorage()).init_app(app)


def test_strict_security_rejects_error_findings_but_not_warnings() -> None:
    missing_secret = configured_app(secret_key=None)
    missing_secret.config["MS_ENTRA_STRICT_SECURITY"] = True
    with pytest.raises(ConfigurationError, match="secret-key-missing"):
        MicrosoftEntraAuth().init_app(missing_secret)

    warning_only = configured_app(secret_key="short")
    warning_only.config["MS_ENTRA_STRICT_SECURITY"] = True
    extension = MicrosoftEntraAuth()
    extension.init_app(warning_only)
    assert extension.audit_security(warning_only).passed is True
    assert extension.audit_security(warning_only).hardened is False


def test_extension_audit_supports_explicit_and_current_application() -> None:
    app = configured_app()
    extension = MicrosoftEntraAuth()
    extension.init_app(app)

    explicit = extension.audit_security(app)
    with app.app_context():
        current = extension.audit_security()

    assert explicit == current
    assert app.extensions["ms_entra_auth"].security_report is current
    with pytest.raises(TypeError, match="Flask"):
        extension.audit_security("not-an-app")  # type: ignore[arg-type]
