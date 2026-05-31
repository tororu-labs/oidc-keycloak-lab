from __future__ import annotations

import base64
import json

from auth import build_user_summary, decode_jwt_payload, sanitize_next_path


def _make_token(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{encoded}.signature"


def test_decode_jwt_payload_none():
    assert decode_jwt_payload(None) == {}


def test_decode_jwt_payload_no_dot():
    assert decode_jwt_payload("notajwt") == {}


def test_decode_jwt_payload_valid():
    payload = {"sub": "user-123", "preferred_username": "alice"}
    result = decode_jwt_payload(_make_token(payload))
    assert result["sub"] == "user-123"
    assert result["preferred_username"] == "alice"


def test_decode_jwt_payload_invalid_base64():
    assert decode_jwt_payload("header.!!!.sig") == {}


def test_sanitize_next_path_none():
    assert sanitize_next_path(None) == "/me"


def test_sanitize_next_path_no_leading_slash():
    assert sanitize_next_path("admin") == "/me"


def test_sanitize_next_path_absolute_url_http():
    assert sanitize_next_path("http://evil.com/steal") == "/me"


def test_sanitize_next_path_absolute_url_https():
    assert sanitize_next_path("https://evil.com") == "/me"


def test_sanitize_next_path_valid_paths():
    assert sanitize_next_path("/admin") == "/admin"
    assert sanitize_next_path("/me") == "/me"
    assert sanitize_next_path("/api/me") == "/api/me"


def test_build_user_summary_from_access_claims():
    access_claims = {
        "sub": "user-123",
        "preferred_username": "alice",
        "realm_access": {"roles": ["user", "admin"]},
        "iss": "http://keycloak/realm",
        "scope": "openid profile",
    }
    result = build_user_summary(access_claims, {})
    assert result["sub"] == "user-123"
    assert result["preferred_username"] == "alice"
    assert "admin" in result["roles"]
    assert result["issuer"] == "http://keycloak/realm"


def test_build_user_summary_fallback_to_id_claims():
    id_claims = {"sub": "user-456", "preferred_username": "bob", "iss": "http://keycloak/realm"}
    result = build_user_summary({}, id_claims)
    assert result["sub"] == "user-456"
    assert result["preferred_username"] == "bob"


def test_build_user_summary_unknown_username_when_empty():
    result = build_user_summary({}, {})
    assert result["preferred_username"] == "unknown"
