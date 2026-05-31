from __future__ import annotations

from typing import Any

from auth import build_claim_summary
from config import Settings
from fastapi.responses import JSONResponse


# 日本語をそのまま返せる JSON レスポンス設定。
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


# ルートごとの JSON 生成を分けて、endpoint 本体を薄くする。
def build_index_response(settings: Settings) -> dict[str, Any]:
    return {
        "name": "demo-api",
        "issuer": settings.issuer,
        "expected_audience": settings.expected_audience,  # 08: aud 検証のために追加
        "protected_routes": ["/me", "/admin-data"],
        # 07: "verification": ["signature", "iss", "exp"],  # 08 で aud 追加により置き換え
        # 07: "note": "この段階では audience 検証は行わない。",  # 08 で aud 検証追加により不要
        "verification": ["signature", "iss", "exp", "aud"],  # 08: aud を追加
    }


def build_me_response(claims: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": "Access Token を検証できました。",
        "user": build_claim_summary(claims),
    }


def build_admin_response(claims: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": "admin role を確認できました。",
        "resource": "backend-api protected admin data",
        "user": build_claim_summary(claims),
    }
