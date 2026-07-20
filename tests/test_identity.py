from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType
from typing import Any

import pytest

from flask_ms_entra_auth import Identity, IdentityValidationError


def valid_claims() -> dict[str, object]:
    return {
        "oid": " object-id ",
        "tid": "tenant-id",
        "sub": "subject-id",
        "name": "Vitor Oliveira",
        "preferred_username": "vitor@example.com",
        "roles": ["Reader", "Writer"],
        "metadata": {"active": True, "level": 3},
    }


def test_identity_from_claims_normalizes_expected_fields() -> None:
    identity = Identity.from_claims(
        valid_claims(),
        home_account_id=" home-id ",
        expected_tenant_id="TENANT-ID",
    )

    assert identity.object_id == "object-id"
    assert identity.tenant_id == "tenant-id"
    assert identity.subject == "subject-id"
    assert identity.home_account_id == "home-id"
    assert identity.display_name == "Vitor Oliveira"
    assert identity.username == "vitor@example.com"
    assert identity.stable_id == ("tenant-id", "object-id")


def test_username_falls_back_to_upn_and_optional_claims_can_be_absent() -> None:
    identity = Identity.from_claims(
        {"oid": "object-id", "tid": "tenant-id", "upn": "legacy@example.com"},
        home_account_id="home-id",
    )

    assert identity.subject is None
    assert identity.display_name is None
    assert identity.username == "legacy@example.com"


def test_preferred_username_takes_precedence_over_upn() -> None:
    claims = valid_claims()
    claims["upn"] = "fallback@example.com"

    identity = Identity.from_claims(claims, home_account_id="home-id")

    assert identity.username == "vitor@example.com"


def test_identity_claims_are_deeply_read_only_and_detached() -> None:
    claims = valid_claims()
    identity = Identity.from_claims(claims, home_account_id="home-id")
    claims["oid"] = "changed"
    roles = claims["roles"]
    assert isinstance(roles, list)
    roles.append("Changed")

    assert isinstance(identity.claims, MappingProxyType)
    assert identity.claims["oid"] == " object-id "
    assert identity.claims["roles"] == ("Reader", "Writer")
    nested = identity.claims["metadata"]
    assert isinstance(nested, MappingProxyType)
    assert nested["active"] is True

    with pytest.raises(TypeError):
        identity.claims["oid"] = "blocked"  # type: ignore[index]
    with pytest.raises(TypeError):
        nested["active"] = False  # type: ignore[index]


def test_identity_dataclass_is_frozen_and_repr_is_sanitized() -> None:
    identity = Identity.from_claims(valid_claims(), home_account_id="home-id")

    with pytest.raises(FrozenInstanceError):
        identity.object_id = "changed"  # type: ignore[misc]

    representation = repr(identity)
    assert representation == "Identity(authenticated=True)"
    assert "Vitor" not in representation
    assert "home-id" not in representation


@pytest.mark.parametrize(
    "claim",
    ["access_token", "refresh_token", "id_token", "client_secret", "token_cache"],
)
def test_identity_rejects_credential_claims(claim: str) -> None:
    claims = valid_claims()
    claims[claim] = "secret-value"

    with pytest.raises(IdentityValidationError, match="must not contain credentials"):
        Identity.from_claims(claims, home_account_id="home-id")


@pytest.mark.parametrize("key", ["oid", "tid"])
@pytest.mark.parametrize("value", [None, "", "   ", 123])
def test_required_identity_claims_must_be_non_empty_strings(key: str, value: object) -> None:
    claims = valid_claims()
    claims[key] = value

    with pytest.raises(IdentityValidationError, match=key):
        Identity.from_claims(claims, home_account_id="home-id")


@pytest.mark.parametrize("key", ["sub", "name", "preferred_username", "upn"])
@pytest.mark.parametrize("value", ["", "   ", 123])
def test_optional_identity_claims_are_validated_when_present(key: str, value: object) -> None:
    claims = valid_claims()
    claims.pop("preferred_username", None)
    claims[key] = value

    with pytest.raises(IdentityValidationError, match=key):
        Identity.from_claims(claims, home_account_id="home-id")


def test_identity_rejects_unexpected_tenant() -> None:
    with pytest.raises(IdentityValidationError, match="tenant does not match"):
        Identity.from_claims(
            valid_claims(),
            home_account_id="home-id",
            expected_tenant_id="other-tenant",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("object_id", ""),
        ("tenant_id", 123),
        ("home_account_id", " "),
        ("subject", 123),
        ("display_name", ""),
        ("username", object()),
    ],
)
def test_direct_identity_construction_validates_fields(field: str, value: object) -> None:
    kwargs: dict[str, Any] = {
        "object_id": "object-id",
        "tenant_id": "tenant-id",
        "home_account_id": "home-id",
    }
    kwargs[field] = value

    with pytest.raises(IdentityValidationError, match="identity field"):
        Identity(**kwargs)


def test_claims_must_be_a_mapping() -> None:
    invalid_claims: Any = ["not", "a", "mapping"]

    with pytest.raises(IdentityValidationError, match="must be a mapping"):
        Identity.from_claims(invalid_claims, home_account_id="home-id")


@pytest.mark.parametrize("invalid_key", ["", 123])
def test_claim_names_must_be_non_empty_strings(invalid_key: object) -> None:
    claims: dict[Any, object] = {
        "oid": "object-id",
        "tid": "tenant-id",
        invalid_key: "x",
    }

    with pytest.raises(IdentityValidationError, match="claim names"):
        Identity.from_claims(claims, home_account_id="home-id")


def test_nested_claim_names_must_be_strings() -> None:
    claims = valid_claims()
    claims["nested"] = {123: "invalid"}

    with pytest.raises(IdentityValidationError, match="nested identity claim names"):
        Identity.from_claims(claims, home_account_id="home-id")


def test_claim_values_must_be_json_compatible() -> None:
    claims = valid_claims()
    claims["unsupported"] = object()

    with pytest.raises(IdentityValidationError, match="JSON-compatible"):
        Identity.from_claims(claims, home_account_id="home-id")


def test_username_is_none_when_no_username_claim_exists() -> None:
    identity = Identity.from_claims(
        {"oid": "object-id", "tid": "tenant-id"},
        home_account_id="home-id",
    )

    assert identity.username is None
