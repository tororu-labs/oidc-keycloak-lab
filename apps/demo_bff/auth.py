from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx
from joserfc import jwt as joserfc_jwt
from joserfc.jwk import KeySet

if TYPE_CHECKING:
    from config import Settings

# back-channel logout イベントの識別子（OpenID Connect 仕様）
_BACKCHANNEL_LOGOUT_EVENT = "http://schemas.openid.net/event/backchannel-logout"


class LogoutTokenError(Exception):
    pass


async def verify_logout_token(token_str: str, settings: Settings) -> str:
    """logout token の署名と claims を検証し、keycloak_sid を返す。"""
    jwks_uri = f"{settings.issuer}/protocol/openid-connect/certs"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(jwks_uri)
            resp.raise_for_status()
        key_set = KeySet.import_key_set(resp.json())
    except Exception as exc:
        raise LogoutTokenError(f"JWKS の取得に失敗しました: {exc}") from exc

    try:
        token = joserfc_jwt.decode(token_str, key_set)
        claims = token.claims
    except Exception as exc:
        raise LogoutTokenError(f"logout token の署名検証に失敗しました: {exc}") from exc

    # events claim に backchannel-logout イベントが含まれていることを確認する
    events = claims.get("events", {})
    if _BACKCHANNEL_LOGOUT_EVENT not in events:
        raise LogoutTokenError("events claim に backchannel-logout イベントが含まれていません")

    # nonce は logout token に含めてはならない（OpenID Connect Back-Channel Logout 仕様）
    if "nonce" in claims:
        raise LogoutTokenError("logout token に nonce が含まれています（仕様違反）")

    sid = claims.get("sid")
    if not sid:
        raise LogoutTokenError("logout token に sid claim が含まれていません")

    return sid


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
