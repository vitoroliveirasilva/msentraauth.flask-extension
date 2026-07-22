from __future__ import annotations

import json
from typing import cast

import pytest
from flask import Flask, session

from flask_ms_entra_auth import (
    AuthenticationRequired,
    Identity,
    IdentityValidationError,
    MemoryStorage,
    StorageError,
    TokenAcquisitionError,
)
from flask_ms_entra_auth.auth.service import _access_token_from_result, _select_account
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.context import get_current_identity
from flask_ms_entra_auth.web import session as session_module
from flask_ms_entra_auth.web.session import WebSessionManager


def _config() -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="client-secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="final-production-hardening",
        token_cache_ttl=7_200,
        flow_ttl=600,
        identity_ttl=7_200,
    )


def _identity(*, object_id: str = "object-id") -> Identity:
    return Identity.from_claims(
        {"oid": object_id, "tid": "tenant-id"},
        home_account_id=f"home-{object_id}",
        expected_tenant_id="tenant-id",
    )


def _notes(error: BaseException) -> list[str]:
    return cast(list[str], getattr(error, "__notes__", []))


def test_identity_rejects_core_claims_that_disagree_with_validated_fields() -> None:
    with pytest.raises(IdentityValidationError, match="claim 'oid' does not match"):
        Identity(
            object_id="validated-object",
            tenant_id="tenant-id",
            home_account_id="home-id",
            claims={"oid": "different-object", "tid": "tenant-id"},
        )

    with pytest.raises(IdentityValidationError, match="claim 'tid' does not match"):
        Identity(
            object_id="object-id",
            tenant_id="validated-tenant",
            home_account_id="home-id",
            claims={"oid": "object-id", "tid": "different-tenant"},
        )


def test_identity_allows_missing_core_claims_for_direct_constructor_compatibility() -> None:
    identity = Identity(
        object_id="object-id",
        tenant_id="tenant-id",
        home_account_id="home-id",
    )

    assert identity.claims == {}


@pytest.mark.parametrize(
    "credential_key",
    [
        "Refresh-Token",
        "refreshToken",
        "CLIENT SECRET",
        "\uff52\uff45\uff46\uff52\uff45\uff53\uff48\uff3f\uff54\uff4f\uff4b\uff45\uff4e",
    ],
)
def test_identity_rejects_canonicalized_credential_claim_names(
    credential_key: str,
) -> None:
    claims = {
        "oid": "object-id",
        "tid": "tenant-id",
        "nested": {credential_key: "must-not-survive"},
    }

    with pytest.raises(IdentityValidationError, match="must not contain credentials"):
        Identity.from_claims(claims, home_account_id="home-id")


class AdjustableClock:
    def __init__(self) -> None:
        self.value = 100.0
        self.error: Exception | None = None

    def __call__(self) -> float:
        if self.error is not None:
            raise self.error
        return self.value


def test_memory_take_does_not_destroy_value_when_clock_fails() -> None:
    clock = AdjustableClock()
    storage = MemoryStorage(clock=clock)
    storage.save("key", b"value", ttl=60)
    clock.error = RuntimeError("clock unavailable")

    with pytest.raises(StorageError, match="expiration check"):
        storage.take("key")

    clock.error = None
    assert storage.load("key") == b"value"


def test_memory_storage_wraps_expiration_overflow_without_writing() -> None:
    storage = MemoryStorage(clock=lambda: 1.0)

    with pytest.raises(StorageError, match="expiration calculation") as raised:
        storage.save("key", b"value", ttl=10**400)

    assert isinstance(raised.value.__cause__, OverflowError)
    assert storage.load("key") is None


def test_memory_storage_rejects_non_finite_expiration_without_writing() -> None:
    storage = MemoryStorage(clock=lambda: 1e308)

    with pytest.raises(StorageError, match="expiration calculation") as raised:
        storage.save("key", b"value", ttl=10**308)

    assert isinstance(raised.value.__cause__, ValueError)
    assert storage.load("key") is None


class SelectiveDeleteFailureStorage(MemoryStorage):
    def __init__(self, *, fail_all_deletes: bool = False) -> None:
        super().__init__()
        self.fail_key: str | None = None
        self.fail_all_deletes = fail_all_deletes

    def delete(self, key: str) -> None:
        if self.fail_all_deletes or key == self.fail_key:
            raise StorageError("identity deletion failed")
        super().delete(key)


def _session_app() -> Flask:
    app = Flask("session-final-hardening")
    app.secret_key = "s" * 32
    app.extensions["ms_entra_auth"] = object()
    return app


def test_identity_rotation_rolls_back_new_payload_when_old_delete_fails() -> None:
    app = _session_app()
    storage = SelectiveDeleteFailureStorage()
    manager = WebSessionManager(_config(), storage)
    first_identity = _identity(object_id="first")

    with app.test_request_context("/"):
        manager.establish_identity(first_identity)
        previous_metadata = dict(session[manager.session_key])
        previous_key = session_module._identity_key(previous_metadata["session_id"])
        storage.fail_key = previous_key

        with pytest.raises(StorageError, match="identity deletion failed"):
            manager.establish_identity(_identity(object_id="replacement"))

        assert dict(session[manager.session_key]) == previous_metadata
        assert storage.load(previous_key) is not None
        assert get_current_identity() == first_identity
        assert len(storage._entries) == 1


def test_identity_rotation_preserves_primary_error_when_rollback_cleanup_fails() -> None:
    app = _session_app()
    storage = SelectiveDeleteFailureStorage()
    manager = WebSessionManager(_config(), storage)

    with app.test_request_context("/"):
        manager.establish_identity(_identity(object_id="first"))
        storage.fail_all_deletes = True

        with pytest.raises(StorageError, match="identity deletion failed") as raised:
            manager.establish_identity(_identity(object_id="replacement"))

    assert _notes(raised.value) == ["new identity cleanup also failed"]


def test_restore_removes_corrupt_identity_payload_and_browser_reference() -> None:
    app = _session_app()
    storage = MemoryStorage()
    manager = WebSessionManager(_config(), storage)
    session_id = "corrupt-session"
    identity_key = session_module._identity_key(session_id)

    with app.test_request_context("/"):
        storage.save(identity_key, b"{", ttl=600)
        session[manager.session_key] = {"session_id": session_id}

        with pytest.raises(StorageError, match="could not be decoded"):
            manager.restore_identity()

        assert manager.session_key not in session
        assert storage.load(identity_key) is None


def test_restore_preserves_corruption_error_when_payload_cleanup_fails() -> None:
    app = _session_app()
    storage = SelectiveDeleteFailureStorage(fail_all_deletes=True)
    manager = WebSessionManager(_config(), storage)
    session_id = "corrupt-session"
    identity_key = session_module._identity_key(session_id)

    with app.test_request_context("/"):
        storage.save(identity_key, b"{", ttl=600)
        session[manager.session_key] = {"session_id": session_id}

        with pytest.raises(StorageError, match="could not be decoded") as raised:
            manager.restore_identity()

        assert manager.session_key not in session

    assert _notes(raised.value) == ["corrupt identity cleanup also failed"]


def test_stored_identity_rejects_inconsistent_core_claims() -> None:
    payload = json.dumps(
        {
            "object_id": "validated-object",
            "tenant_id": "tenant-id",
            "home_account_id": "home-id",
            "subject": None,
            "display_name": None,
            "username": None,
            "claims": {"oid": "different-object", "tid": "tenant-id"},
        }
    ).encode()

    with pytest.raises(StorageError, match="failed validation"):
        session_module._deserialize_identity(payload, expected_tenant_id="tenant-id")


def test_silent_account_selection_rejects_ambiguous_cache_entries() -> None:
    accounts = (
        {"home_account_id": "home-id"},
        {"home_account_id": "home-id"},
    )

    with pytest.raises(AuthenticationRequired, match="multiple matching"):
        _select_account(accounts, "home-id")


def test_silent_token_result_rejects_whitespace_only_access_token() -> None:
    with pytest.raises(TokenAcquisitionError, match="no access token"):
        _access_token_from_result({"access_token": "   "})
