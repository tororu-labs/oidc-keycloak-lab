from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from authlib.jose import JsonWebKey, jwt
from authlib.jose.errors import BadSignatureError, ExpiredTokenError, JoseError
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class Settings:
    keycloak_base_url: str
    keycloak_realm: str
    jwks_cache_ttl_seconds: int
    clock_skew_seconds: int

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_base_url}/realms/{self.keycloak_realm}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/certs"


class JwksCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.expires_at = 0.0
        self.key_set: Any = None

    def get(self) -> Any | None:
        if self.key_set is None:
            return None
        if self.expires_at <= time.time():
            self.clear()
            return None
        return self.key_set

    def set(self, key_set: Any) -> Any:
        self.key_set = key_set
        self.expires_at = time.time() + self.ttl_seconds
        return key_set

    def clear(self) -> None:
        self.key_set = None
        self.expires_at = 0.0


def load_settings() -> Settings:
    return Settings(
        keycloak_base_url=os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/"),
        keycloak_realm=os.getenv("KEYCLOAK_REALM", "lab"),
        jwks_cache_ttl_seconds=int(os.getenv("JWKS_CACHE_TTL_SECONDS", "300")),
        clock_skew_seconds=int(os.getenv("CLOCK_SKEW_SECONDS", "30")),
    )


settings = load_settings()


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(title="FastAPI Backend API Demo", default_response_class=UTF8JSONResponse)
app.state.jwks_cache = JwksCache(settings.jwks_cache_ttl_seconds)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": 'Bearer realm="demo-api"'},
    )


def extract_roles(claims: dict[str, Any]) -> list[str]:
    roles = claims.get("realm_access", {}).get("roles", [])
    if isinstance(roles, list):
        return [str(role) for role in roles]
    return []


def build_claim_summary(claims: dict[str, Any]) -> dict[str, Any]:
    return {
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "azp": claims.get("azp"),
        "iss": claims.get("iss"),
        "scope": claims.get("scope"),
        "roles": extract_roles(claims),
        "exp": claims.get("exp"),
        "iat": claims.get("iat"),
    }


def parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise unauthorized("Authorization ヘッダーがありません。")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized("Bearer token の形式が不正です。")
    return token


async def load_jwks(force_refresh: bool = False) -> Any:
    cache: JwksCache = app.state.jwks_cache
    if not force_refresh:
        cached = cache.get()
        if cached is not None:
            return cached

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.jwks_url)
            response.raise_for_status()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Keycloak の JWKS を取得できませんでした。"
                f" Keycloak が停止している可能性があります。 detail={exc}"
            ),
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Keycloak の JWKS 応答が不正です。 status={exc.response.status_code}",
        ) from exc

    return cache.set(JsonWebKey.import_key_set(response.json()))


async def verify_access_token(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    token = parse_bearer_token(authorization)
    claims_options = {"iss": {"essential": True, "value": settings.issuer}}

    for attempt in range(2):
        key_set = await load_jwks(force_refresh=attempt == 1)
        try:
            claims = jwt.decode(token, key_set, claims_options=claims_options)
            claims.validate(leeway=settings.clock_skew_seconds)
            return dict(claims)
        except BadSignatureError:
            if attempt == 0:
                app.state.jwks_cache.clear()
                continue
            raise unauthorized("Access Token の署名検証に失敗しました。")
        except ExpiredTokenError:
            raise unauthorized("Access Token の有効期限が切れています。")
        except JoseError as exc:
            raise unauthorized(f"Access Token を検証できませんでした。 detail={exc}")

    raise unauthorized("Access Token を検証できませんでした。")


async def require_admin_claims(
    claims: dict[str, Any] = Depends(verify_access_token),
) -> dict[str, Any]:
    if "admin" not in extract_roles(claims):
        raise HTTPException(status_code=403, detail="admin role が必要です。")
    return claims


@app.get("/")
async def index() -> dict[str, Any]:
    return {
        "name": "demo-api",
        "issuer": settings.issuer,
        "protected_routes": ["/me", "/admin-data"],
        "verification": ["signature", "iss", "exp"],
        "note": "この段階では audience 検証は行わない。",
    }


@app.get("/me")
async def me(claims: dict[str, Any] = Depends(verify_access_token)) -> dict[str, Any]:
    return {
        "message": "Access Token を検証できました。",
        "user": build_claim_summary(claims),
    }


@app.get("/admin-data")
async def admin_data(
    claims: dict[str, Any] = Depends(require_admin_claims),
) -> dict[str, Any]:
    return {
        "message": "admin role を確認できました。",
        "resource": "backend-api protected admin data",
        "user": build_claim_summary(claims),
    }
