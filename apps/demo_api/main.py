from __future__ import annotations

from typing import Any

from auth import build_require_admin_claims, build_verify_access_token
from config import load_settings
from fastapi import Depends, FastAPI
from telemetry import setup_telemetry
from fastapi.middleware.cors import CORSMiddleware
from jwks_cache import JwksCache
from responses import UTF8JSONResponse, build_admin_response, build_index_response, build_me_response

# 起動時に設定を読み込み、JWT 検証に使う部品をここで配線する。
settings = load_settings()

app = FastAPI(title="FastAPI Backend API Demo", default_response_class=UTF8JSONResponse)
setup_telemetry(app)

# SPA（demo-web-spa）からのブラウザ直接アクセスを許可する。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)

app.state.jwks_cache = JwksCache(settings.jwks_cache_ttl_seconds)

verify_access_token = build_verify_access_token(settings, app.state.jwks_cache)
require_admin_claims = build_require_admin_claims(verify_access_token)


# ここから下は Backend API の endpoint 定義。
@app.get("/")
async def index() -> dict[str, Any]:
    return build_index_response(settings)


@app.get("/me")
async def me(claims: dict[str, Any] = Depends(verify_access_token)) -> dict[str, Any]:
    return build_me_response(claims)


@app.get("/admin-data")
async def admin_data(
    claims: dict[str, Any] = Depends(require_admin_claims),
) -> dict[str, Any]:
    return build_admin_response(claims)
