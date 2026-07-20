from __future__ import annotations

from collections.abc import Callable

import pytest

from flask_ms_entra_auth import AuthStorage, MemoryStorage
from flask_ms_entra_auth.storage.namespaced import NamespacedStorage

StorageFactory = Callable[[], AuthStorage]


def _memory_factory() -> AuthStorage:
    return MemoryStorage()


def _namespaced_factory() -> AuthStorage:
    return NamespacedStorage(MemoryStorage(), "contract")


@pytest.fixture(params=[_memory_factory, _namespaced_factory])
def storage(request: pytest.FixtureRequest) -> AuthStorage:
    factory: StorageFactory = request.param
    return factory()


def test_storage_contract_loads_absent_key_as_none(storage: AuthStorage) -> None:
    assert storage.load("missing") is None


def test_storage_contract_saves_and_loads_bytes(storage: AuthStorage) -> None:
    storage.save("flow", b"serialized-flow")

    assert storage.load("flow") == b"serialized-flow"


def test_storage_contract_uses_last_write_wins(storage: AuthStorage) -> None:
    storage.save("cache", b"first")
    storage.save("cache", b"second")

    assert storage.load("cache") == b"second"


def test_storage_contract_delete_is_idempotent(storage: AuthStorage) -> None:
    storage.save("identity", b"value")

    storage.delete("identity")
    storage.delete("identity")

    assert storage.load("identity") is None
