from dataclasses import FrozenInstanceError

import pytest

from flask_ms_entra_auth import (
    AuthenticationRejected,
    AuthEvent,
    HookExecutionError,
    Identity,
    LocalBindingError,
    StorageError,
)
from flask_ms_entra_auth.hooks import HookRegistry


def identity() -> Identity:
    return Identity.from_claims(
        {"oid": "object-id", "tid": "tenant-id"},
        home_account_id="home-id",
        expected_tenant_id="tenant-id",
    )


def event() -> AuthEvent:
    return AuthEvent(
        name="authentication_succeeded",
        timestamp=1.5,
        request_id="request-1",
        endpoint="ms_entra_auth.callback",
        method="GET",
        duration_ms=2.5,
    )


def test_event_is_immutable_and_contains_only_explicit_metadata() -> None:
    value = event()

    assert value.name == "authentication_succeeded"
    assert value.error_code is None
    with pytest.raises(FrozenInstanceError):
        value.name = "changed"  # type: ignore[misc]


def test_hook_registration_is_ordered_idempotent_and_decorator_friendly() -> None:
    registry = HookRegistry()
    called: list[str] = []

    @registry.on_authenticated
    def first(value: Identity) -> None:
        assert value.object_id == "object-id"
        called.append("first")

    registry.on_authenticated(first)

    @registry.on_authenticated
    def second(value: Identity) -> None:
        del value
        called.append("second")

    registry.emit_authenticated(identity())

    assert called == ["first", "second"]


@pytest.mark.parametrize(
    "registration",
    [
        HookRegistry().on_authenticated,
        HookRegistry().on_logout,
        HookRegistry().on_error,
        HookRegistry().on_event,
    ],
)
def test_hook_registration_requires_callable(registration: object) -> None:
    with pytest.raises(TypeError, match="callable"):
        registration(None)  # type: ignore[operator]


def test_authenticated_hook_can_reject_without_wrapping() -> None:
    registry = HookRegistry()

    @registry.on_authenticated
    def reject(value: Identity) -> None:
        del value
        raise AuthenticationRejected("local account is disabled")

    with pytest.raises(AuthenticationRejected, match="disabled"):
        registry.emit_authenticated(identity())


def test_authenticated_hook_failure_becomes_local_binding_error_with_cause() -> None:
    registry = HookRegistry()

    @registry.on_authenticated
    def broken(value: Identity) -> None:
        del value
        raise RuntimeError("private database detail")

    with pytest.raises(LocalBindingError, match="bound locally") as raised:
        registry.emit_authenticated(identity())

    assert raised.value.event == "authenticated"
    assert isinstance(raised.value.__cause__, RuntimeError)
    assert "private database detail" not in str(raised.value)


def test_logout_hooks_receive_optional_identity_and_wrap_failures() -> None:
    registry = HookRegistry()
    received: list[Identity | None] = []
    registry.on_logout(received.append)

    registry.emit_logout(identity())
    registry.emit_logout(None)
    assert [item.object_id if item else None for item in received] == [
        "object-id",
        None,
    ]

    @registry.on_logout
    def broken(value: Identity | None) -> None:
        del value
        raise RuntimeError("private logout detail")

    with pytest.raises(HookExecutionError, match="logout hook failed") as raised:
        registry.emit_logout(None)
    assert raised.value.event == "logout"
    assert isinstance(raised.value.__cause__, RuntimeError)


def test_error_hooks_do_not_replace_original_error_and_report_failures() -> None:
    registry = HookRegistry()
    error = StorageError("safe")
    received: list[StorageError] = []

    @registry.on_error
    def collect(value: object) -> None:
        assert value is error
        received.append(error)

    @registry.on_error
    def broken(value: object) -> None:
        del value
        raise RuntimeError("ignored")

    assert registry.emit_error(error) == 1
    assert received == [error]


def test_event_hooks_use_snapshot_and_do_not_affect_authentication() -> None:
    registry = HookRegistry()
    received: list[str] = []

    def late(value: AuthEvent) -> None:
        received.append(f"late:{value.name}")

    @registry.on_event
    def first(value: AuthEvent) -> None:
        received.append(value.name)
        registry.on_event(late)

    @registry.on_event
    def broken(value: AuthEvent) -> None:
        del value
        raise RuntimeError("ignored")

    assert registry.emit_event(event()) == 1
    assert received == ["authentication_succeeded"]
    assert registry.emit_event(event()) == 1
    assert received[-2:] == [
        "authentication_succeeded",
        "late:authentication_succeeded",
    ]
