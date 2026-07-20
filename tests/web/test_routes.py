from __future__ import annotations

import pytest
from flask import Flask

from flask_ms_entra_auth import (
    AuthenticationRequired,
    ConfigurationError,
    IdentityValidationError,
    InvalidNavigationTarget,
    MicrosoftEntraAuthError,
    StorageError,
    TokenAcquisitionError,
)
from flask_ms_entra_auth.web.routes import (
    _error_status_and_message,
    _single_query_value,
)


def test_login_rejects_duplicate_navigation_targets() -> None:
    app = Flask("route-parser")

    with (
        app.test_request_context("/auth/login?next=/one&next=/two"),
        pytest.raises(InvalidNavigationTarget, match="at most once"),
    ):
        _single_query_value("next")


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (AuthenticationRequired("required"), (401, "Authentication is required.")),
        (
            TokenAcquisitionError("token"),
            (502, "Authentication could not be completed."),
        ),
        (
            StorageError("storage"),
            (503, "Authentication service is temporarily unavailable."),
        ),
        (
            ConfigurationError("configuration"),
            (500, "Authentication is not configured correctly."),
        ),
        (
            IdentityValidationError("identity"),
            (400, "Authentication could not be completed."),
        ),
    ],
)
def test_route_errors_are_translated_without_internal_details(
    error: MicrosoftEntraAuthError,
    expected: tuple[int, str],
) -> None:
    assert _error_status_and_message(error) == expected
