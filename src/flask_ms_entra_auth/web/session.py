from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from secrets import token_urlsafe
from typing import Final

from flask import current_app, session

from ..config import MicrosoftEntraAuthConfig
from ..context import bind_identity, clear_identity, get_current_identity
from ..errors import (
    AuthenticationRequired,
    ConfigurationError,
    IdentityValidationError,
    InvalidCallbackError,
    StorageError,
)
from ..identity import Identity
from ..storage import AtomicAuthStorage, AuthStorage

_SESSION_PREFIX: Final = "_msentra_"
_SESSION_ID_BYTES: Final = 32
_MAX_SESSION_ID_LENGTH: Final = 128
_MAX_IDENTITY_PAYLOAD_BYTES: Final = 262_144


class WebSessionManager:
    # Persiste autenticação sem colocar claims ou tokens em cookies

    __slots__ = ("_config", "_session_key", "_storage")

    def __init__(self, config: MicrosoftEntraAuthConfig, storage: AuthStorage) -> None:
        self._config = config
        self._storage = storage
        digest = sha256(config.session_namespace.encode("utf-8")).hexdigest()[:16]
        self._session_key = f"{_SESSION_PREFIX}{digest}"

    @property
    def session_key(self) -> str:
        # Retorna a chave de sessão Flask de propriedade do pacote
        return self._session_key

    def require_secure_session(self) -> None:
        # Falha antes de gravar referências de autenticação quando o Flask não pode assinar sua sessão
        if not current_app.secret_key:
            raise ConfigurationError("Flask SECRET_KEY must be configured for web authentication")

    def set_pending_flow(self, flow_id: str) -> None:
        # Associa um fluxo do lado do servidor com a sessão do navegador atual
        self.require_secure_session()
        metadata = self._metadata()
        metadata["flow_id"] = _validate_session_identifier(flow_id)
        self._write_metadata(metadata)

    def consume_pending_flow(self) -> str:
        # Remove e retorna o identificador de fluxo pendente exatamente uma vez
        self.require_secure_session()
        metadata = self._metadata()
        flow_id = metadata.pop("flow_id", None)
        self._write_metadata(metadata)
        if not isinstance(flow_id, str):
            raise InvalidCallbackError("authentication flow is missing or already consumed")
        try:
            return _validate_session_identifier(flow_id)
        except StorageError as exc:
            raise InvalidCallbackError("authentication flow reference is invalid") from exc

    def discard_pending_flow(self) -> str | None:
        # Remove um fluxo pendente do lado do servidor, se houver, sem falhar
        metadata = self._metadata()
        flow_id = metadata.pop("flow_id", None)
        self._write_metadata(metadata)
        if not isinstance(flow_id, str):
            return None
        try:
            return _validate_session_identifier(flow_id)
        except StorageError:
            return None

    def establish_identity(self, identity: Identity) -> None:
        # Rotaciona a sessão de autenticação interna e persiste uma identidade validada
        if not isinstance(identity, Identity):
            msg = "identity must be an instance of Identity"
            raise TypeError(msg)
        self.require_secure_session()

        payload = _serialize_identity(identity)
        session_id = token_urlsafe(_SESSION_ID_BYTES)
        metadata = self._metadata()
        old_session_id = metadata.get("session_id")
        validated_old_session_id: str | None = None
        if isinstance(old_session_id, str):
            try:
                validated_old_session_id = _validate_session_identifier(old_session_id)
            except StorageError:
                validated_old_session_id = None

        previous_identity: Identity | None = None
        if validated_old_session_id is not None:
            try:
                previous_identity = get_current_identity()
            except AuthenticationRequired:
                previous_identity = None

        new_identity_key = _identity_key(session_id)
        self._storage.save(
            new_identity_key,
            payload,
            ttl=self._config.identity_ttl,
        )
        try:
            self._write_metadata({"session_id": session_id})
            bind_identity(identity)
            if validated_old_session_id is not None:
                self._storage.delete(_identity_key(validated_old_session_id))
        except Exception as exc:
            rollback_metadata = metadata if validated_old_session_id is not None else {}
            try:
                self._write_metadata(rollback_metadata)
            except Exception:
                exc.add_note("authentication session metadata cleanup also failed")
            try:
                self._storage.delete(new_identity_key)
            except Exception:
                exc.add_note("new identity cleanup also failed")
            try:
                if previous_identity is None:
                    clear_identity()
                else:
                    bind_identity(previous_identity)
            except Exception:
                exc.add_note("request identity cleanup also failed")
            raise

    def restore_identity(self) -> Identity | None:
        # Carrega e vincula a identidade do lado do servidor atual quando existir
        clear_identity()
        metadata = self._metadata()
        session_id = metadata.get("session_id")
        if not isinstance(session_id, str):
            return None

        try:
            validated_session_id = _validate_session_identifier(session_id)
        except StorageError:
            self._write_metadata({})
            return None

        identity_key = _identity_key(validated_session_id)
        payload = self._storage.load(identity_key)
        if payload is None:
            self._write_metadata({})
            return None

        try:
            identity = _deserialize_identity(
                payload,
                expected_tenant_id=self._config.tenant_id,
            )
        except StorageError as exc:
            try:
                self._write_metadata({})
            except Exception:
                exc.add_note("corrupt identity metadata cleanup also failed")
            try:
                self._storage.delete(identity_key)
            except Exception:
                exc.add_note("corrupt identity cleanup also failed")
            raise
        bind_identity(identity)
        return identity

    def clear_authentication(self) -> Identity | None:
        # Remove a identidade atual sem consumir fluxos pendentes da mesma sessão
        identity: Identity | None = None
        metadata = self._metadata()
        reference_revoked = False
        try:
            session_id = metadata.get("session_id")
            if not isinstance(session_id, str):
                reference_revoked = True
                return None
            try:
                validated_session_id = _validate_session_identifier(session_id)
            except StorageError:
                reference_revoked = True
                return None

            identity_key = _identity_key(validated_session_id)
            if isinstance(self._storage, AtomicAuthStorage):
                payload = self._storage.take(identity_key)
            else:
                payload = self._storage.load(identity_key)
                if payload is not None:
                    self._storage.delete(identity_key)
            reference_revoked = True
            if payload is not None:
                identity = _deserialize_identity(
                    payload,
                    expected_tenant_id=self._config.tenant_id,
                )
            return identity
        finally:
            try:
                if reference_revoked:
                    metadata.pop("session_id", None)
                    self._write_metadata(metadata)
            finally:
                clear_identity()

    def _metadata(self) -> dict[str, str]:
        raw = session.get(self._session_key)
        if not isinstance(raw, Mapping):
            return {}

        metadata: dict[str, str] = {}
        for key in ("session_id", "flow_id"):
            value = raw.get(key)
            if isinstance(value, str):
                metadata[key] = value
        return metadata

    def _write_metadata(self, metadata: Mapping[str, str]) -> None:
        try:
            if metadata:
                session[self._session_key] = dict(metadata)
            else:
                session.pop(self._session_key, None)
        except Exception as exc:
            raise StorageError("authentication session metadata update failed") from exc


def _identity_key(session_id: str) -> str:
    digest = sha256(session_id.encode("utf-8")).hexdigest()
    return f"identity:{digest}"


def _validate_session_identifier(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > _MAX_SESSION_ID_LENGTH
        or not value.isascii()
        or any(not (character.isalnum() or character in "_-") for character in value)
    ):
        raise StorageError("authentication session identifier is invalid")
    return value


def _serialize_identity(identity: Identity) -> bytes:
    payload = {
        "object_id": identity.object_id,
        "tenant_id": identity.tenant_id,
        "home_account_id": identity.home_account_id,
        "subject": identity.subject,
        "display_name": identity.display_name,
        "username": identity.username,
        "claims": _thaw_json_value(identity.claims),
    }
    try:
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (RecursionError, TypeError, ValueError, UnicodeError) as exc:
        raise StorageError("identity could not be serialized") from exc
    if len(serialized) > _MAX_IDENTITY_PAYLOAD_BYTES:
        raise StorageError("identity exceeds the supported storage size")
    return serialized


def _deserialize_identity(payload: bytes, *, expected_tenant_id: str) -> Identity:
    if len(payload) > _MAX_IDENTITY_PAYLOAD_BYTES:
        raise StorageError("stored identity exceeds the supported storage size")
    try:
        data = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, RecursionError, UnicodeError) as exc:
        raise StorageError("stored identity could not be decoded") from exc
    if not isinstance(data, Mapping):
        raise StorageError("stored identity has an invalid structure")

    claims = data.get("claims")
    if not isinstance(claims, Mapping):
        raise StorageError("stored identity has invalid claims")

    object_id = _stored_required_text(data, "object_id")
    tenant_id = _stored_required_text(data, "tenant_id")
    home_account_id = _stored_required_text(data, "home_account_id")
    subject = _stored_optional_text(data, "subject")
    display_name = _stored_optional_text(data, "display_name")
    username = _stored_optional_text(data, "username")

    try:
        identity = Identity(
            object_id=object_id,
            tenant_id=tenant_id,
            home_account_id=home_account_id,
            subject=subject,
            display_name=display_name,
            username=username,
            claims=claims,
        )
    except IdentityValidationError as exc:
        raise StorageError("stored identity failed validation") from exc
    if identity.tenant_id.casefold() != expected_tenant_id.casefold():
        raise StorageError("stored identity belongs to another tenant")
    return identity


def _thaw_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


def _stored_required_text(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise StorageError("stored identity has an invalid structure")
    return value


def _stored_optional_text(data: Mapping[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise StorageError("stored identity has an invalid structure")
    return value
