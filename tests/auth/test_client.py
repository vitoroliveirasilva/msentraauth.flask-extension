from __future__ import annotations

from typing import Any

from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth.auth import client as client_module
from flask_ms_entra_auth.auth.client import create_confidential_client
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig


def config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="app",
        token_cache_ttl=3600,
    )


def test_default_client_factory_passes_safe_msal_configuration(
    monkeypatch: Any,
) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(client_module, "ConfidentialClientApplication", fake_client)
    cache = SerializableTokenCache()

    result = create_confidential_client(config(), cache)

    assert result is sentinel
    assert captured == {
        "client_id": "client-id",
        "client_credential": "client-secret",
        "authority": "https://login.microsoftonline.com/tenant-id",
        "token_cache": cache,
        "enable_pii_log": False,
    }
