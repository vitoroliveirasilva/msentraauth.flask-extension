from __future__ import annotations

from typing import Any

import pytest
from msal import SerializableTokenCache  # type: ignore[import-untyped]

from flask_ms_entra_auth import MemoryStorage, StorageError
from flask_ms_entra_auth.auth.token_cache import (
    delete_token_cache,
    load_token_cache,
    persist_token_cache,
    token_cache_key,
)


class RecordingStorage(MemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self.saved: list[tuple[str, bytes, int | None]] = []
        self.deleted: list[str] = []

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        self.saved.append((key, value, ttl))
        super().save(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        super().delete(key)


def test_token_cache_key_is_stable_hashed_and_contains_no_account_id() -> None:
    first = token_cache_key("user-id.tenant-id")
    second = token_cache_key(" user-id.tenant-id ")

    assert first == second
    assert first.startswith("token-cache:")
    assert "user-id" not in first
    assert len(first) == len("token-cache:") + 64


@pytest.mark.parametrize("value", [None, "", "   ", 123])
def test_token_cache_key_rejects_invalid_account_identifier(value: object) -> None:
    invalid: Any = value

    with pytest.raises(StorageError, match="home account identifier"):
        token_cache_key(invalid)


def test_load_absent_token_cache_returns_clean_serializable_cache() -> None:
    cache = load_token_cache(MemoryStorage(), "home-id")

    assert isinstance(cache, SerializableTokenCache)
    assert cache.serialize() == "{}"
    assert cache.has_state_changed is False


def test_load_deserializes_existing_cache() -> None:
    storage = MemoryStorage()
    source = SerializableTokenCache()
    source.has_state_changed = True
    serialized = source.serialize().encode()
    storage.save(token_cache_key("home-id"), serialized)

    cache = load_token_cache(storage, "home-id")

    assert cache.serialize() == "{}"
    assert cache.has_state_changed is False


def test_load_rejects_non_utf8_cache_without_exposing_content() -> None:
    storage = MemoryStorage()
    storage.save(token_cache_key("home-id"), b"\xffsecret-cache")

    with pytest.raises(StorageError, match="could not be deserialized") as captured:
        load_token_cache(storage, "home-id")

    assert isinstance(captured.value.__cause__, UnicodeDecodeError)
    assert "secret-cache" not in str(captured.value)


def test_load_rejects_invalid_serialized_cache() -> None:
    storage = MemoryStorage()
    storage.save(token_cache_key("home-id"), b"not-json")

    with pytest.raises(StorageError, match="could not be deserialized") as captured:
        load_token_cache(storage, "home-id")

    assert captured.value.__cause__ is not None


def test_unchanged_cache_is_not_persisted() -> None:
    storage = RecordingStorage()
    cache = SerializableTokenCache()

    changed = persist_token_cache(storage, "home-id", cache, ttl=3600)

    assert changed is False
    assert storage.saved == []


def test_changed_cache_is_serialized_with_ttl() -> None:
    storage = RecordingStorage()
    cache = SerializableTokenCache()
    cache.has_state_changed = True

    changed = persist_token_cache(storage, "home-id", cache, ttl=3600)

    assert changed is True
    assert len(storage.saved) == 1
    key, value, ttl = storage.saved[0]
    assert key == token_cache_key("home-id")
    assert value == b"{}"
    assert ttl == 3600
    assert cache.has_state_changed is False


def test_serialization_failure_is_wrapped_safely() -> None:
    class BrokenCache:
        has_state_changed = True

        def serialize(self) -> str:
            raise ValueError("raw-cache-secret")

    storage = RecordingStorage()
    broken: Any = BrokenCache()

    with pytest.raises(StorageError, match="could not be serialized") as captured:
        persist_token_cache(storage, "home-id", broken, ttl=3600)

    assert isinstance(captured.value.__cause__, ValueError)
    assert "raw-cache-secret" not in str(captured.value)


def test_delete_uses_hashed_account_key_and_is_idempotent() -> None:
    storage = RecordingStorage()
    storage.save(token_cache_key("home-id"), b"{}")

    delete_token_cache(storage, "home-id")
    delete_token_cache(storage, "home-id")

    assert storage.deleted == [token_cache_key("home-id"), token_cache_key("home-id")]
    assert storage.load(token_cache_key("home-id")) is None
