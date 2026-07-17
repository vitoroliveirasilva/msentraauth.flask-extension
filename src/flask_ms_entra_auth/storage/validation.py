from __future__ import annotations

from typing import Final

from ..errors import StorageError

_MAX_KEY_LENGTH: Final = 512
_MAX_NAMESPACE_LENGTH: Final = 128


def validate_key(key: object) -> str:
    # Valida uma chave de armazenamento sem refletir seu valor em mensagens de erro
    if not isinstance(key, str) or not key or len(key) > _MAX_KEY_LENGTH or "\x00" in key:
        raise StorageError("storage key must be a non-empty safe string")
    return key


def validate_value(value: object) -> bytes:
    # Valida e copia defensivamente um valor de armazenamento
    if not isinstance(value, bytes):
        raise StorageError("storage value must be bytes")
    return bytes(value)


def validate_ttl(ttl: object) -> int | None:
    # Vaida um TTL positivo opcional em segundos
    if ttl is None:
        return None
    if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0:
        raise StorageError("storage ttl must be a positive integer or None")
    return ttl


def validate_namespace(namespace: object) -> str:
    # Valida um namespace sem refletir seu valor em mensagens de erro
    if (
        not isinstance(namespace, str)
        or not namespace
        or len(namespace) > _MAX_NAMESPACE_LENGTH
        or "\x00" in namespace
        or any(not (character.isalnum() or character in "._-") for character in namespace)
    ):
        raise StorageError("storage namespace must contain only letters, numbers, '.', '_' or '-'")
    return namespace
