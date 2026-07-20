from __future__ import annotations

from threading import RLock

from ..errors import StorageError
from .base import AtomicAuthStorage, AuthStorage
from .validation import validate_key, validate_namespace, validate_ttl, validate_value


class NamespacedStorage:
    # Prefixa todos os nomes de chave antes de delegar para outro backend de armazenamento

    __slots__ = ("_backend", "_lock", "_namespace", "_prefix")

    def __init__(self, backend: AuthStorage, namespace: str) -> None:
        if not isinstance(backend, AuthStorage):
            msg = "storage must implement AuthStorage"
            raise TypeError(msg)
        self._namespace = validate_namespace(namespace)
        self._backend = backend
        self._prefix = f"msentra:{self._namespace}:"
        self._lock = RLock()

    @property
    def namespace(self) -> str:
        # Retorna o namespace imutável da aplicação
        return self._namespace

    @property
    def backend(self) -> AuthStorage:
        # Retorna o backend encapsulado para inspeção de capacidades
        return self._backend

    @property
    def supports_atomic_take(self) -> bool:
        # Informe se o backend oferece consumo atômico distribuído
        return isinstance(self._backend, AtomicAuthStorage)

    def load(self, key: str) -> bytes | None:
        # Carrega um valor com namespace e valida a resposta do backend
        scoped_key = self._scoped_key(key)
        try:
            value = self._backend.load(scoped_key)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("storage load failed") from exc

        if value is None:
            return None
        return validate_value(value)

    def save(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        # Salva um valor com namespace
        scoped_key = self._scoped_key(key)
        validated_value = validate_value(value)
        validated_ttl = validate_ttl(ttl)
        try:
            self._backend.save(scoped_key, validated_value, ttl=validated_ttl)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("storage save failed") from exc

    def take(self, key: str) -> bytes | None:
        # Consome um valor de forma atômica quando suportado pelo backend
        scoped_key = self._scoped_key(key)
        try:
            if isinstance(self._backend, AtomicAuthStorage):
                value = self._backend.take(scoped_key)
            else:
                with self._lock:
                    value = self._backend.load(scoped_key)
                    if value is not None:
                        self._backend.delete(scoped_key)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("storage atomic consume failed") from exc

        if value is None:
            return None
        return validate_value(value)

    def delete(self, key: str) -> None:
        # Deleta um valor com namespace
        scoped_key = self._scoped_key(key)
        try:
            self._backend.delete(scoped_key)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("storage delete failed") from exc

    def _scoped_key(self, key: str) -> str:
        return f"{self._prefix}{validate_key(key)}"
