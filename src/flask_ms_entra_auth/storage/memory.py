from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from time import monotonic

from ..errors import StorageError
from .validation import validate_key, validate_ttl, validate_value


@dataclass(frozen=True, slots=True)
class _Entry:
    value: bytes
    expires_at: float | None


class MemoryStorage:
    # Armazena valores de byte na memória do processo com expiração opcional

    __slots__ = ("_clock", "_entries", "_lock")

    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._entries: dict[str, _Entry] = {}
        self._lock = RLock()

    def load(self, key: str) -> bytes | None:
        # Carrega uma cópia defensiva de um valor não expirado
        validated_key = validate_key(key)
        with self._lock:
            entry = self._entries.get(validated_key)
            if entry is None:
                return None
            if self._is_expired(entry):
                self._entries.pop(validated_key, None)
                return None
            return bytes(entry.value)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        # Salva uma cópia defensiva usando a semântica de última gravação vence
        validated_key = validate_key(key)
        validated_value = validate_value(value)
        validated_ttl = validate_ttl(ttl)

        try:
            expires_at = None if validated_ttl is None else self._clock() + validated_ttl
        except Exception as exc:
            raise StorageError("storage expiration calculation failed") from exc

        with self._lock:
            self._entries[validated_key] = _Entry(validated_value, expires_at)

    def delete(self, key: str) -> None:
        """Delete a value idempotently."""
        validated_key = validate_key(key)
        with self._lock:
            self._entries.pop(validated_key, None)

    def purge_expired(self) -> int:
        # Remove valores expirados e retorne o número de entradas removidas
        try:
            now = self._clock()
        except Exception as exc:
            raise StorageError("storage expiration cleanup failed") from exc

        with self._lock:
            expired = [
                key
                for key, entry in self._entries.items()
                if entry.expires_at is not None and entry.expires_at <= now
            ]
            for key in expired:
                self._entries.pop(key, None)
            return len(expired)

    def _is_expired(self, entry: _Entry) -> bool:
        if entry.expires_at is None:
            return False
        try:
            return entry.expires_at <= self._clock()
        except Exception as exc:
            raise StorageError("storage expiration check failed") from exc
