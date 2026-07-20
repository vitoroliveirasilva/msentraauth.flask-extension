from __future__ import annotations

import pytest

from flask_ms_entra_auth import AtomicAuthStorage, MemoryStorage, StorageError
from flask_ms_entra_auth.storage.namespaced import NamespacedStorage


class BasicStorage:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.loaded: list[str] = []
        self.deleted: list[str] = []

    def load(self, key: str) -> bytes | None:
        self.loaded.append(key)
        return self.values.get(key)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del ttl
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.values.pop(key, None)


class NativeAtomicStorage(BasicStorage):
    def __init__(self) -> None:
        super().__init__()
        self.taken: list[str] = []

    def take(self, key: str) -> bytes | None:
        self.taken.append(key)
        return self.values.pop(key, None)


class FailingAtomicStorage(NativeAtomicStorage):
    def take(self, key: str) -> bytes | None:
        del key
        raise RuntimeError("private backend detail")


class StorageErrorAtomicStorage(NativeAtomicStorage):
    def take(self, key: str) -> bytes | None:
        del key
        raise StorageError("safe storage error")


class InvalidAtomicStorage(NativeAtomicStorage):
    def take(self, key: str) -> bytes | None:
        del key
        return "invalid"  # type: ignore[return-value]


def test_memory_storage_is_atomic_and_take_is_one_time() -> None:
    storage = MemoryStorage()
    assert isinstance(storage, AtomicAuthStorage)
    storage.save("value", b"payload")

    assert storage.take("value") == b"payload"
    assert storage.take("value") is None
    assert storage.load("value") is None


def test_memory_take_removes_expired_value() -> None:
    now = [10.0]
    storage = MemoryStorage(clock=lambda: now[0])
    storage.save("value", b"payload", ttl=1)
    now[0] = 11.0

    assert storage.take("value") is None
    assert storage.load("value") is None


def test_namespaced_take_uses_native_atomic_backend() -> None:
    backend = NativeAtomicStorage()
    storage = NamespacedStorage(backend, "app")
    storage.save("flow", b"payload")

    assert storage.supports_atomic_take is True
    assert storage.take("flow") == b"payload"
    assert backend.taken == ["msentra:app:flow"]
    assert backend.loaded == []
    assert backend.deleted == []


def test_namespaced_take_uses_compatibility_fallback() -> None:
    backend = BasicStorage()
    storage = NamespacedStorage(backend, "app")
    storage.save("flow", b"payload")

    assert storage.supports_atomic_take is False
    assert storage.take("flow") == b"payload"
    assert storage.take("flow") is None
    assert backend.loaded == ["msentra:app:flow", "msentra:app:flow"]
    assert backend.deleted == ["msentra:app:flow"]


def test_namespaced_take_preserves_storage_error_and_wraps_other_failures() -> None:
    with pytest.raises(StorageError, match="safe storage error"):
        NamespacedStorage(StorageErrorAtomicStorage(), "app").take("flow")

    with pytest.raises(StorageError, match="atomic consume") as captured:
        NamespacedStorage(FailingAtomicStorage(), "app").take("flow")
    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "private backend detail" not in str(captured.value)


def test_namespaced_take_validates_backend_return_value() -> None:
    with pytest.raises(StorageError, match="storage value"):
        NamespacedStorage(InvalidAtomicStorage(), "app").take("flow")
