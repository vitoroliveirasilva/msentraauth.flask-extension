from __future__ import annotations

from hashlib import sha256

from msal import SerializableTokenCache  # type: ignore[import-untyped]

from ..errors import StorageError
from ..storage import AuthStorage


def load_token_cache(storage: AuthStorage, home_account_id: str) -> SerializableTokenCache:
    # Carrega um cache MSAL por conta sem expor a conta em sua chave
    cache = SerializableTokenCache()
    serialized = storage.load(token_cache_key(home_account_id))
    if serialized is None:
        return cache

    try:
        cache.deserialize(serialized.decode("utf-8"))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise StorageError("token cache could not be deserialized") from exc
    return cache


def persist_token_cache(
    storage: AuthStorage,
    home_account_id: str,
    cache: SerializableTokenCache,
    *,
    ttl: int,
) -> bool:
    # Persiste um cache MSAL alterado e informa se ocorreu uma gravação
    if not cache.has_state_changed:
        return False

    try:
        serialized = cache.serialize().encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise StorageError("token cache could not be serialized") from exc
    storage.save(token_cache_key(home_account_id), serialized, ttl=ttl)
    return True


def delete_token_cache(storage: AuthStorage, home_account_id: str) -> None:
    # Deleta um cache de conta sem revelar o identificador da conta
    storage.delete(token_cache_key(home_account_id))


def token_cache_key(home_account_id: str) -> str:
    # Derive uma chave de armazenamento não reversível a partir de um ID de conta principal do MSAL
    if not isinstance(home_account_id, str) or not home_account_id.strip():
        raise StorageError("home account identifier must be a non-empty string")
    digest = sha256(home_account_id.strip().encode("utf-8")).hexdigest()
    return f"token-cache:{digest}"
