from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from typing import Any

import pytest

from flask_ms_entra_auth import AuthStorage, MemoryStorage, StorageError
from flask_ms_entra_auth.storage.namespaced import NamespacedStorage


class AdjustableClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.failure: Exception | None = None

    def __call__(self) -> float:
        if self.failure is not None:
            raise self.failure
        return self.now


class RecordingStorage:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.loaded_keys: list[str] = []
        self.saved_keys: list[str] = []
        self.deleted_keys: list[str] = []

    def load(self, key: str) -> bytes | None:
        self.loaded_keys.append(key)
        return self.values.get(key)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del ttl
        self.saved_keys.append(key)
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.deleted_keys.append(key)
        self.values.pop(key, None)


class FailingStorage:
    def __init__(self, operation: str, error: Exception) -> None:
        self.operation = operation
        self.error = error

    def load(self, key: str) -> bytes | None:
        del key
        if self.operation == "load":
            raise self.error
        return None

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        del key, value, ttl
        if self.operation == "save":
            raise self.error

    def delete(self, key: str) -> None:
        del key
        if self.operation == "delete":
            raise self.error


class InvalidReturnStorage(RecordingStorage):
    def load(self, key: str) -> bytes | None:
        del key
        return "not-bytes"  # type: ignore[return-value]


class IncompleteStorage:
    def load(self, key: str) -> bytes | None:
        del key
        return None


def test_memory_storage_satisfies_runtime_protocol() -> None:
    assert isinstance(MemoryStorage(), AuthStorage)


def test_memory_storage_expires_values_and_removes_them_lazily() -> None:
    clock = AdjustableClock()
    storage = MemoryStorage(clock=clock)
    storage.save("flow", b"value", ttl=10)

    clock.now = 109.9
    assert storage.load("flow") == b"value"

    clock.now = 110.0
    assert storage.load("flow") is None
    assert storage.load("flow") is None


def test_memory_storage_purges_only_expired_values() -> None:
    clock = AdjustableClock()
    storage = MemoryStorage(clock=clock)
    storage.save("short", b"short", ttl=1)
    storage.save("long", b"long", ttl=20)
    storage.save("persistent", b"persistent")
    clock.now = 102.0

    assert storage.purge_expired() == 1
    assert storage.load("short") is None
    assert storage.load("long") == b"long"
    assert storage.load("persistent") == b"persistent"
    assert storage.purge_expired() == 0


def test_memory_storage_last_completed_write_wins_across_threads() -> None:
    storage = MemoryStorage()
    release_last_writer = Event()
    second_finished = Event()

    def delayed_writer() -> None:
        release_last_writer.wait()
        storage.save("cache", b"completed-last")

    def first_writer() -> None:
        storage.save("cache", b"completed-first")
        second_finished.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        delayed = executor.submit(delayed_writer)
        first = executor.submit(first_writer)
        second_finished.wait()
        release_last_writer.set()
        first.result()
        delayed.result()

    assert storage.load("cache") == b"completed-last"


@pytest.mark.parametrize("key", [None, "", "x" * 513, "unsafe\x00key"])
def test_memory_storage_rejects_invalid_keys(key: object) -> None:
    storage = MemoryStorage()
    invalid_key: Any = key

    with pytest.raises(StorageError, match="storage key"):
        storage.load(invalid_key)
    with pytest.raises(StorageError, match="storage key"):
        storage.save(invalid_key, b"value")
    with pytest.raises(StorageError, match="storage key"):
        storage.delete(invalid_key)


@pytest.mark.parametrize("value", [None, "text", bytearray(b"bytes")])
def test_memory_storage_rejects_non_bytes_values(value: object) -> None:
    invalid_value: Any = value

    with pytest.raises(StorageError, match="storage value"):
        MemoryStorage().save("key", invalid_value)


@pytest.mark.parametrize("ttl", [True, False, 0, -1, 1.5, "10"])
def test_memory_storage_rejects_invalid_ttl(ttl: object) -> None:
    invalid_ttl: Any = ttl

    with pytest.raises(StorageError, match="storage ttl"):
        MemoryStorage().save("key", b"value", ttl=invalid_ttl)


def test_memory_storage_wraps_clock_failure_during_save() -> None:
    clock = AdjustableClock()
    clock.failure = RuntimeError("clock secret")

    with pytest.raises(StorageError, match="expiration calculation") as captured:
        MemoryStorage(clock=clock).save("sensitive-key", b"sensitive-value", ttl=1)

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "sensitive" not in str(captured.value)


def test_memory_storage_wraps_clock_failure_during_load() -> None:
    clock = AdjustableClock()
    storage = MemoryStorage(clock=clock)
    storage.save("key", b"value", ttl=1)
    clock.failure = RuntimeError("clock failed")

    with pytest.raises(StorageError, match="expiration check") as captured:
        storage.load("key")

    assert isinstance(captured.value.__cause__, RuntimeError)


def test_memory_storage_wraps_clock_failure_during_cleanup() -> None:
    clock = AdjustableClock()
    storage = MemoryStorage(clock=clock)
    clock.failure = RuntimeError("clock failed")

    with pytest.raises(StorageError, match="expiration cleanup") as captured:
        storage.purge_expired()

    assert isinstance(captured.value.__cause__, RuntimeError)


def test_namespaced_storage_prefixes_all_backend_keys() -> None:
    backend = RecordingStorage()
    storage = NamespacedStorage(backend, "application-one")

    storage.save("flow", b"value", ttl=30)
    assert storage.load("flow") == b"value"
    storage.delete("flow")

    assert backend.saved_keys == ["msentra:application-one:flow"]
    assert backend.loaded_keys == ["msentra:application-one:flow"]
    assert backend.deleted_keys == ["msentra:application-one:flow"]
    assert storage.namespace == "application-one"


def test_namespaces_isolate_apps_on_the_same_backend() -> None:
    backend = MemoryStorage()
    first = NamespacedStorage(backend, "first")
    second = NamespacedStorage(backend, "second")

    first.save("cache", b"first-value")
    second.save("cache", b"second-value")

    assert first.load("cache") == b"first-value"
    assert second.load("cache") == b"second-value"
    first.delete("cache")
    assert second.load("cache") == b"second-value"


@pytest.mark.parametrize(
    "namespace",
    [None, "", "x" * 129, "has space", "has:colon", "unsafe\x00namespace"],
)
def test_namespaced_storage_rejects_invalid_namespace(namespace: object) -> None:
    invalid_namespace: Any = namespace

    with pytest.raises(StorageError, match="storage namespace"):
        NamespacedStorage(MemoryStorage(), invalid_namespace)


def test_namespaced_storage_rejects_incomplete_backend() -> None:
    invalid_backend: Any = IncompleteStorage()

    with pytest.raises(TypeError, match="AuthStorage"):
        NamespacedStorage(invalid_backend, "valid")


@pytest.mark.parametrize(
    ("operation", "expected_message"),
    [
        ("load", "storage load failed"),
        ("save", "storage save failed"),
        ("delete", "storage delete failed"),
    ],
)
def test_namespaced_storage_wraps_backend_failures(operation: str, expected_message: str) -> None:
    original = RuntimeError("backend included sensitive material")
    storage = NamespacedStorage(FailingStorage(operation, original), "application")

    with pytest.raises(StorageError, match=expected_message) as captured:
        if operation == "load":
            storage.load("secret-key")
        elif operation == "save":
            storage.save("secret-key", b"secret-value")
        else:
            storage.delete("secret-key")

    assert captured.value.__cause__ is original
    assert "secret" not in str(captured.value)


def test_namespaced_storage_preserves_existing_storage_error() -> None:
    original = StorageError("safe backend failure")
    storage = NamespacedStorage(FailingStorage("load", original), "application")

    with pytest.raises(StorageError) as captured:
        storage.load("key")

    assert captured.value is original


def test_namespaced_storage_rejects_invalid_backend_return() -> None:
    storage = NamespacedStorage(InvalidReturnStorage(), "application")

    with pytest.raises(StorageError, match="storage value"):
        storage.load("key")


@pytest.mark.parametrize("operation", ["save", "delete"])
def test_namespaced_storage_preserves_existing_storage_error_for_writes(
    operation: str,
) -> None:
    original = StorageError("safe backend failure")
    storage = NamespacedStorage(FailingStorage(operation, original), "application")

    with pytest.raises(StorageError) as captured:
        if operation == "save":
            storage.save("key", b"value")
        else:
            storage.delete("key")

    assert captured.value is original
