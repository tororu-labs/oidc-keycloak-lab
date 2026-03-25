from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import urlparse


# 署名検証はせず、説明用に JWT の payload 部分だけを読む。
def decode_jwt_payload(token: str | None) -> dict[str, Any]:
    if not token:
        return {}

    parts = token.split(".")
    if len(parts) < 2:
        return {}

    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return {}


# Access Token と ID Token から、画面表示に必要な最小情報を抜き出す。
def build_user_summary(access_claims: dict[str, Any], id_claims: dict[str, Any]) -> dict[str, Any]:
    roles = access_claims.get("realm_access", {}).get("roles", [])
    return {
        "sub": access_claims.get("sub") or id_claims.get("sub"),
        "preferred_username": (
            access_claims.get("preferred_username")
            or id_claims.get("preferred_username")
            or access_claims.get("email")
            or "unknown"
        ),
        "roles": roles,
        "issuer": access_claims.get("iss") or id_claims.get("iss"),
        "scope": access_claims.get("scope"),
    }


# ログイン後の戻り先は、アプリ内の安全な path だけ許可する。
def sanitize_next_path(candidate: str | None) -> str:
    if not candidate:
        return "/me"
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return "/me"
    if not candidate.startswith("/"):
        return "/me"
    return candidate
