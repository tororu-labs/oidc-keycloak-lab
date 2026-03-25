from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from auth import build_claim_summary
from config import Settings


# 日本語をそのまま返せる JSON レスポンス設定。
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


# ルートごとの JSON 生成を分けて、endpoint 本体を薄くする。
def build_index_response(settings: Settings) -> dict[str, Any]:
    return {
        "name": "demo-api",
        "issuer": settings.issuer,
        "protected_routes": ["/me", "/admin-data"],
        "verification": ["signature", "iss", "exp"],
        "note": "この段階では audience 検証は行わない。",
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
