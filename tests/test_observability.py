from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest
from flask import Flask

from flask_ms_entra_auth import (
    AuthenticationCancelled,
    AuthenticationRejected,
    StorageError,
    TokenAcquisitionError,
)
from flask_ms_entra_auth.config import MicrosoftEntraAuthConfig
from flask_ms_entra_auth.hooks import AuthEvent, HookRegistry
from flask_ms_entra_auth.observability import Observability, _safe_request_id


def config(
    *, event_logging: bool = False, header: str = "X-Request-ID"
) -> MicrosoftEntraAuthConfig:
    return MicrosoftEntraAuthConfig(
        client_id="client-id",
        client_secret="secret",
        tenant_id="tenant-id",
        redirect_uri="https://app.example.com/auth/callback",
        authority="https://login.microsoftonline.com/tenant-id",
        scopes=("User.Read",),
        session_namespace="tests",
        token_cache_ttl=100,
        event_logging=event_logging,
        request_id_header=header,
    )


@pytest.fixture
def app() -> Iterator[Flask]:
    value = Flask("observability-test")
    value.testing = True
    with value.app_context():
        yield value


def test_emit_outside_request_context_rounds_duration_and_dispatches_hook() -> None:
    registry = HookRegistry()
    received: list[AuthEvent] = []
    registry.on_event(received.append)
    observer = Observability(config(), registry, logging.getLogger("test.observer"))

    event = observer.emit("token_acquired", duration_ms=-3.14159)

    assert event.endpoint is None
    assert event.method is None
    assert event.request_id is None
    assert event.duration_ms == 0.0
    assert received == [event]


def test_request_id_uses_valid_header_and_is_cached_per_request(app: Flask) -> None:
    registry = HookRegistry()
    observer = Observability(config(header="X-Correlation-ID"), registry, logging.getLogger("test"))

    with app.test_request_context(
        "/resource",
        headers={"X-Correlation-ID": " request_ABC:123 "},
        method="POST",
    ):
        first = observer.emit("first")
        second = observer.emit("second")

    assert first.request_id == "request_ABC:123"
    assert second.request_id == first.request_id
    assert first.endpoint is None
    assert first.method == "POST"


def test_invalid_request_id_is_replaced_with_random_identifier(
    app: Flask, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "flask_ms_entra_auth.observability.token_hex", lambda size: f"generated-{size}"
    )
    observer = Observability(config(), HookRegistry(), logging.getLogger("test"))

    with app.test_request_context("/", headers={"X-Request-ID": "unsafe value!"}):
        event = observer.emit("authentication_started")

    assert event.request_id == "generated-16"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (123, None),
        ("", None),
        ("   ", None),
        ("x" * 129, None),
        ("bad value", None),
        ("safe._:-123", "safe._:-123"),
    ],
)
def test_safe_request_id_validation(value: object, expected: str | None) -> None:
    assert _safe_request_id(value) == expected


def test_structured_logging_contains_only_normalized_metadata(
    app: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    registry = HookRegistry()

    @registry.on_event
    def broken(event: AuthEvent) -> None:
        del event
        raise RuntimeError("private hook detail")

    logger = logging.getLogger("flask_ms_entra_auth.test")
    observer = Observability(config(event_logging=True), registry, logger)
    error = TokenAcquisitionError(
        "safe",
        code="invalid_grant",
        correlation_id="corr-123",
    )

    with (
        caplog.at_level(logging.INFO, logger=logger.name),
        app.test_request_context("/callback", headers={"X-Request-ID": "req-123"}),
    ):
        event = observer.emit("authentication_error", duration_ms=1.23456, error=error)

    record = caplog.records[-1]
    assert event.duration_ms == 1.235
    assert record.auth_event == "authentication_error"  # type: ignore[attr-defined]
    assert record.auth_request_id == "req-123"  # type: ignore[attr-defined]
    assert record.auth_error_code == "TokenAcquisitionError"  # type: ignore[attr-defined]
    assert record.auth_correlation_id == "corr-123"  # type: ignore[attr-defined]
    assert record.auth_hook_failures == 1  # type: ignore[attr-defined]
    assert "invalid_grant" not in record.getMessage()
    assert "private hook detail" not in record.getMessage()


@pytest.mark.parametrize(
    ("error", "event_name"),
    [
        (AuthenticationCancelled("cancelled"), "authentication_cancelled"),
        (AuthenticationRejected("rejected"), "authentication_rejected"),
        (StorageError("storage"), "storage_failure"),
        (TokenAcquisitionError("token"), "authentication_error"),
    ],
)
def test_emit_error_maps_event_and_notifies_only_once(
    error: Exception,
    event_name: str,
) -> None:
    registry = HookRegistry()
    errors: list[object] = []
    events: list[str] = []
    registry.on_error(errors.append)
    registry.on_event(lambda event: events.append(event.name))
    observer = Observability(config(), registry, logging.getLogger("test"))

    observer.emit_error(error)  # type: ignore[arg-type]
    observer.emit_error(error)  # type: ignore[arg-type]

    assert errors == [error]
    assert events == [event_name]


def test_error_hook_failure_is_logged_without_masking_original(
    app: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    registry = HookRegistry()

    @registry.on_error
    def broken(error: object) -> None:
        del error
        raise RuntimeError("ignored secret")

    logger = logging.getLogger("flask_ms_entra_auth.test.error")
    observer = Observability(config(event_logging=True), registry, logger)
    error = StorageError("safe")

    with (
        caplog.at_level(logging.INFO, logger=logger.name),
        app.test_request_context("/"),
    ):
        observer.emit_error(error)

    assert [record.levelno for record in caplog.records] == [
        logging.INFO,
        logging.WARNING,
    ]
    assert caplog.records[-1].auth_event == "error_hook_failed"  # type: ignore[attr-defined]
    assert "ignored secret" not in caplog.text
