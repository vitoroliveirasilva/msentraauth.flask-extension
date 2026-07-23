from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
from flask import Flask, session
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import (
    AuthenticationRequired,
    Identity,
    MemoryStorage,
    MicrosoftEntraAuth,
    StorageError,
)
from flask_ms_entra_auth.auth import token_cache as token_cache_module
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.context import get_current_identity
from flask_ms_entra_auth.web import session as session_module
from flask_ms_entra_auth.web.session import WebSessionManager


def config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="terminal-hardening",
        token_cache_ttl=300,
    )


def app() -> Flask:
    application = Flask("terminal-hardening")
    application.testing = True
    application.secret_key = "terminal-hardening-secret-key-32-bytes"
    application.extensions["ms_entra_auth"] = object()
    return application


def identity() -> Identity:
    return Identity.from_claims(
        {"oid": "object-id", "tid": "tenant-id"},
        home_account_id="home-id",
        expected_tenant_id="tenant-id",
    )


class FailingTakeStorage(MemoryStorage):
    fail_take = False

    def take(self, key: str) -> bytes | None:
        if self.fail_take and (key.startswith("identity:") or ":identity:" in key):
            raise StorageError("identity removal failed")
        return super().take(key)


def test_clear_authentication_preserves_pending_flow() -> None:
    application = app()
    manager = WebSessionManager(config(), MemoryStorage())

    with application.test_request_context("/"):
        manager.establish_identity(identity())
        manager.set_pending_flow("pending-flow")

        removed = manager.clear_authentication()

        assert removed is not None
        assert removed.object_id == "object-id"
        assert session[manager.session_key] == {"flow_id": "pending-flow"}
        with pytest.raises(AuthenticationRequired):
            get_current_identity()


def test_clear_authentication_preserves_retry_state_on_storage_failure() -> None:
    application = app()
    storage = FailingTakeStorage()
    manager = WebSessionManager(config(), storage)

    with application.test_request_context("/"):
        manager.establish_identity(identity())
        manager.set_pending_flow("pending-flow")
        original_metadata = dict(session[manager.session_key])
        storage.fail_take = True

        with pytest.raises(StorageError, match="identity removal failed"):
            manager.clear_authentication()

        assert dict(session[manager.session_key]) == original_metadata
        with pytest.raises(AuthenticationRequired):
            get_current_identity()

        storage.fail_take = False
        removed = manager.clear_authentication()
        assert removed is not None
        assert removed.object_id == "object-id"
        assert session[manager.session_key] == {"flow_id": "pending-flow"}


def test_logout_keeps_retryable_state_when_identity_storage_fails() -> None:
    application = Flask("logout-retry-hardening")
    application.testing = True
    application.secret_key = "logout-retry-hardening-secret-key"
    application.config.from_mapping(
        MS_ENTRA_CLIENT_ID="client-id",
        MS_ENTRA_CLIENT_SECRET="client-secret",
        MS_ENTRA_TENANT_ID="tenant-id",
        MS_ENTRA_REDIRECT_URI="https://app.example.com/auth/callback",
        MS_ENTRA_SESSION_NAMESPACE="logout-retry-hardening",
        MS_ENTRA_AUTO_REGISTER_ROUTES=False,
    )
    storage = FailingTakeStorage()
    extension = MicrosoftEntraAuth(storage=storage)
    extension.init_app(application)
    state = application.extensions["ms_entra_auth"]

    with application.test_request_context("/"):
        state.web_session.establish_identity(identity())
        state.web_session.set_pending_flow("pending-flow")
        original_metadata = dict(session[state.web_session.session_key])
        storage.fail_take = True

        with pytest.raises(StorageError, match="identity removal failed"):
            extension.logout()

        assert dict(session[state.web_session.session_key]) == original_metadata
        with pytest.raises(AuthenticationRequired):
            get_current_identity()


def test_metadata_failure_does_not_leave_request_identity_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = app()
    manager = WebSessionManager(config(), MemoryStorage())

    with application.test_request_context("/"):
        manager.establish_identity(identity())

        def fail_write(self: WebSessionManager, metadata: Mapping[str, str]) -> None:
            del self, metadata
            raise RuntimeError("session metadata write failed")

        monkeypatch.setattr(WebSessionManager, "_write_metadata", fail_write)

        with pytest.raises(RuntimeError, match="metadata write"):
            manager.clear_authentication()
        with pytest.raises(AuthenticationRequired):
            get_current_identity()


def test_session_backend_errors_are_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = app()
    manager = WebSessionManager(config(), MemoryStorage())

    class FailingSession(dict[str, object]):
        def __setitem__(self, key: str, value: object) -> None:
            del key, value
            raise RuntimeError("session backend failed")

    monkeypatch.setattr(session_module, "session", FailingSession())

    with (
        application.test_request_context("/"),
        pytest.raises(
            StorageError,
            match="metadata update failed",
        ),
    ):
        manager._write_metadata({"flow_id": "pending-flow"})


def test_corrupt_identity_error_survives_metadata_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = app()
    storage = MemoryStorage()
    manager = WebSessionManager(config(), storage)

    with application.test_request_context("/"):
        session_id = "corrupt-session"
        session[manager.session_key] = {"session_id": session_id}
        storage.save(session_module._identity_key(session_id), b"not-json", ttl=60)

        def fail_write(self: WebSessionManager, metadata: Mapping[str, str]) -> None:
            del self, metadata
            raise RuntimeError("session metadata cleanup failed")

        monkeypatch.setattr(WebSessionManager, "_write_metadata", fail_write)

        with pytest.raises(StorageError, match="could not be decoded") as captured:
            manager.restore_identity()

    assert getattr(captured.value, "__notes__", []) == [
        "corrupt identity metadata cleanup also failed",
    ]


def test_recursive_identity_payload_fails_as_storage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_loads(payload: str) -> object:
        del payload
        raise RecursionError("nested payload")

    monkeypatch.setattr(json, "loads", fail_loads)

    with pytest.raises(StorageError, match="could not be decoded"):
        session_module._deserialize_identity(b"{}", expected_tenant_id="tenant-id")


def test_recursive_token_cache_payloads_are_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = MemoryStorage()
    storage.save(token_cache_module.token_cache_key("home-id"), b"{}")

    class RecursiveDeserializeCache:
        def deserialize(self, payload: str) -> None:
            del payload
            raise RecursionError("nested token cache")

    monkeypatch.setattr(
        token_cache_module,
        "SerializableTokenCache",
        RecursiveDeserializeCache,
    )
    with pytest.raises(StorageError, match="could not be deserialized"):
        token_cache_module.load_token_cache(storage, "home-id")

    class RecursiveSerializeCache:
        has_state_changed = True

        def serialize(self) -> str:
            raise RecursionError("nested token cache")

    cache = cast(SerializableTokenCache, RecursiveSerializeCache())
    with pytest.raises(StorageError, match="could not be serialized"):
        token_cache_module.persist_token_cache(storage, "home-id", cache, ttl=60)


def test_release_workflow_requires_production_ancestry() -> None:
    workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "release.yml").read_text()

    assert "fetch-depth: 0" in workflow
    assert "if: github.event_name == 'release'" in workflow
    assert "git fetch --no-tags origin prod:refs/remotes/origin/prod" in workflow
    assert 'git merge-base --is-ancestor "$GITHUB_SHA" refs/remotes/origin/prod' in workflow
