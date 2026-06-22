from __future__ import annotations

import logging
from typing import Any

import httpx
from config import Settings
from fastapi import Depends, Header, HTTPException
from joserfc import jwt
from joserfc.errors import BadSignatureError, ExpiredTokenError, JoseError
from joserfc.jwk import KeySet
from jwks_cache import JwksCache
from opentelemetry import trace

logger = logging.getLogger("uvicorn.error")


# 401 のときの返し方を 1 か所にそろえる。
def unauthorized(detail: str, error_stage: str = "backend_authentication") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"message": detail, "error_stage": error_stage},
        headers={"WWW-Authenticate": 'Bearer realm="demo-api"'},
    )


# token から realm role の一覧だけを取り出す。
def extract_roles(claims: dict[str, Any]) -> list[str]:
    roles = claims.get("realm_access", {}).get("roles", [])
    if isinstance(roles, list):
        return [str(role) for role in roles]
    return []


# 画面や JSON に出したい claim だけを抜き出して整形する。
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


# Authorization ヘッダーから Bearer token 文字列だけを取り出す。
def parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        logger.warning("stage=backend_authentication reason=missing_authorization_header")
        raise unauthorized("Authorization ヘッダーがありません。")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        logger.warning("stage=backend_authentication reason=invalid_bearer_format")
        raise unauthorized("Bearer token の形式が不正です。")
    return token


# Keycloak の JWKS を取得し、必要ならキャッシュを更新する。
async def load_jwks(
    settings: Settings,
    cache: JwksCache,
    force_refresh: bool = False,
) -> Any:
    if not force_refresh:
        cached = cache.get()
        if cached is not None:
            return cached

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.jwks_url)
            response.raise_for_status()
    except httpx.RequestError as exc:
        logger.warning("stage=keycloak_jwks detail=%s", str(exc))
        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    f"Keycloak の JWKS を取得できませんでした。 Keycloak が停止している可能性があります。 detail={exc}"
                ),
                "error_stage": "keycloak_jwks",
            },
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "stage=keycloak_jwks status=%s",
            exc.response.status_code,
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": f"Keycloak の JWKS 応答が不正です。 status={exc.response.status_code}",
                "error_stage": "keycloak_jwks",
            },
        ) from exc

    return cache.set(KeySet.import_key_set(response.json()))


# FastAPI の Depends で使える token 検証関数を組み立てる。
def build_verify_access_token(settings: Settings, cache: JwksCache):
    async def verify_access_token(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        token = parse_bearer_token(authorization)
        # 07: claims_options = {"iss": {"essential": True, "value": settings.issuer}}  # 08 で aud 追加により置き換え
        # 08: aud 検証を追加。joserfc の JWTClaimsRegistry で iss / aud を宣言する。
        # leeway は JWTClaimsRegistry に渡す（authlib の claims.validate(leeway=...) に相当）。
        registry = jwt.JWTClaimsRegistry(
            iss={"essential": True, "value": settings.issuer},
            aud={"essential": True, "value": settings.expected_audience},
            leeway=settings.clock_skew_seconds,
        )

        for attempt in range(2):
            key_set = await load_jwks(settings, cache, force_refresh=attempt == 1)
            try:
                # joserfc では kid 不一致も BadSignatureError（JoseError）として扱われるため、
                # authlib 時代の except ValueError ブロックは不要になった。
                result = jwt.decode(token, key_set)
                registry.validate(result.claims)
                logger.info(
                    "stage=backend_authentication_success user=%s iss=%s aud=%s roles=%s",
                    result.claims.get("preferred_username"),
                    result.claims.get("iss"),
                    result.claims.get("aud"),
                    extract_roles(result.claims),
                )
                span = trace.get_current_span()
                if span.is_recording():
                    span.set_attribute("auth.user.id", result.claims.get("sub", ""))
                    span.set_attribute("auth.result", "success")
                    span.set_attribute("auth.user.email", result.claims.get("email", ""))
                return result.claims
            except BadSignatureError:
                if attempt == 0:
                    cache.clear()
                    continue
                logger.warning("stage=backend_authentication reason=bad_signature")
                span = trace.get_current_span()
                if span.is_recording():
                    span.set_attribute("auth.result", "failure")
                    span.set_attribute("auth.failure.reason", "invalid_sig")
                raise unauthorized("Access Token の署名検証に失敗しました。")
            except ExpiredTokenError:
                logger.warning("stage=backend_authentication reason=expired_token")
                span = trace.get_current_span()
                if span.is_recording():
                    span.set_attribute("auth.result", "failure")
                    span.set_attribute("auth.failure.reason", "expired")
                raise unauthorized("Access Token の有効期限が切れています。")
            except JoseError as exc:
                logger.warning("stage=backend_authentication reason=jose_error detail=%s", str(exc))
                span = trace.get_current_span()
                if span.is_recording():
                    span.set_attribute("auth.result", "failure")
                    span.set_attribute("auth.failure.reason", "jose_error")
                raise unauthorized(f"Access Token を検証できませんでした。 detail={exc}")

        logger.warning("stage=backend_authentication reason=unknown_verification_error")
        raise unauthorized("Access Token を検証できませんでした。")

    return verify_access_token


# admin role を要求する依存関数を組み立てる。
def build_require_admin_claims(verify_access_token):
    async def require_admin_claims(
        claims: dict[str, Any] = Depends(verify_access_token),
    ) -> dict[str, Any]:
        if "admin" not in extract_roles(claims):
            logger.info(
                "stage=backend_authorization user=%s roles=%s required_role=admin",
                claims.get("preferred_username"),
                extract_roles(claims),
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "admin role が必要です。",
                    "error_stage": "backend_authorization",
                },
            )
        return claims

    return require_admin_claims
