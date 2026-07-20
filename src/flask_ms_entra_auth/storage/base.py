from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthStorage(Protocol):
    # Minimo contrato de almacenamiento orientado a bytes

    def load(self, key: str) -> bytes | None:
        # Carrega um valor ou retorna ``None`` quando não existe
        ...

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        # Persiste um valor com um TTL positivo opcional em segundos
        ...

    def delete(self, key: str) -> None:
        # Remove um valor sem falhar quando ele já está ausente
        ...


@runtime_checkable
class AtomicAuthStorage(AuthStorage, Protocol):
    # Capacidade de armazenamento opcional para consumo atômico único

    def take(self, key: str) -> bytes | None:
        # Retorna e remove atomicamente um valor quando presente
        ...
