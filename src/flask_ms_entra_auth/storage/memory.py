from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
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
        expires_at = self._expiration_time(validated_ttl)

        with self._lock:
            self._entries[validated_key] = _Entry(validated_value, expires_at)

    def take(self, key: str) -> bytes | None:
        # Retorna e remove um valor não expirado
        validated_key = validate_key(key)
        with self._lock:
            entry = self._entries.get(validated_key)
            if entry is None:
                return None
            if self._is_expired(entry):
                self._entries.pop(validated_key, None)
                return None
            self._entries.pop(validated_key, None)
            return bytes(entry.value)

    def delete(self, key: str) -> None:
        # Deleta um valor imdepotente
        validated_key = validate_key(key)
        with self._lock:
            self._entries.pop(validated_key, None)

    def purge_expired(self) -> int:
        # Remove valores expirados e retorna o número de entradas removidas
        now = self._clock_value("storage expiration cleanup failed")

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
        return entry.expires_at <= self._clock_value("storage expiration check failed")

    def _expiration_time(self, ttl: int | None) -> float | None:
        if ttl is None:
            return None
        try:
            expires_at = self._clock_value("storage expiration calculation failed") + ttl
            if not isfinite(expires_at):
                raise ValueError("storage expiration must be finite")
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("storage expiration calculation failed") from exc
        return expires_at

    def _clock_value(self, error_message: str) -> float:
        try:
            value = self._clock()
            if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
                raise ValueError("storage clock must return a finite number")
        except Exception as exc:
            raise StorageError(error_message) from exc
        return float(value)
