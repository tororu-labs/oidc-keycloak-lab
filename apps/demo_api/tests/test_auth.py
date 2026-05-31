from __future__ import annotations

import pytest
from auth import build_claim_summary, extract_roles, parse_bearer_token
from fastapi import HTTPException


def test_parse_bearer_token_missing_header():
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token(None)
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_invalid_scheme():
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token("Basic abc123")
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_missing_token_value():
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token("Bearer ")
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_valid():
    token = parse_bearer_token("Bearer mytoken.abc.xyz")
    assert token == "mytoken.abc.xyz"


def test_extract_roles_empty_claims():
    assert extract_roles({}) == []


def test_extract_roles_no_realm_access():
    assert extract_roles({"sub": "user-1"}) == []


def test_extract_roles_with_roles():
    claims = {"realm_access": {"roles": ["admin", "user"]}}
    assert extract_roles(claims) == ["admin", "user"]


def test_extract_roles_non_list_is_ignored():
    claims = {"realm_access": {"roles": "admin"}}
    assert extract_roles(claims) == []


def test_build_claim_summary_structure():
    claims = {
        "sub": "user-123",
        "preferred_username": "alice",
        "azp": "demo-client",
        "iss": "http://keycloak/realm",
        "scope": "openid profile",
        "realm_access": {"roles": ["user"]},
        "exp": 9999999,
        "iat": 1000000,
    }
    summary = build_claim_summary(claims)
    assert summary["sub"] == "user-123"
    assert summary["preferred_username"] == "alice"
    assert summary["roles"] == ["user"]
    assert summary["azp"] == "demo-client"
    assert summary["exp"] == 9999999
