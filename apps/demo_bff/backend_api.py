from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi.responses import JSONResponse

from config import Settings


logger = logging.getLogger("uvicorn.error")


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


def build_backend_json_response(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return UTF8JSONResponse(payload, status_code=status_code)


# BFF から Backend API へ Access Token 付きで代理呼び出しする。
async def fetch_backend_api_result(
    settings: Settings,
    session_info: dict[str, Any],
    path: str,
) -> tuple[dict[str, Any], int]:
    access_token = session_info.get("access_token")
    username = session_info["user"]["preferred_username"]
    if not access_token:
        logger.warning(
            "stage=bff_proxy_session_error user=%s path=%s reason=no_access_token",
            username,
            path,
        )
        return (
            {
                "error_stage": "bff_proxy_session_error",
                "detail": "session から access token を取得できませんでした。",
                "path": path,
            },
            500,
        )

    target_url = f"{settings.backend_api_base_url}{path}"
    logger.info(
        "stage=bff_proxy_request user=%s path=%s target_url=%s access_token_present=%s",
        username,
        path,
        target_url,
        True,
    )
    try:
        async with httpx.AsyncClient(timeout=settings.backend_api_timeout_seconds) as client:
            response = await client.get(
                target_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
    except httpx.RequestError as exc:
        logger.warning(
            "stage=bff_proxy_connection_error user=%s path=%s target_url=%s detail=%s",
            username,
            path,
            target_url,
            str(exc),
        )
        return (
            {
                "error_stage": "backend_connection",
                "detail": "Backend API への接続に失敗しました。",
                "backend_url": target_url,
                "error": str(exc),
            },
            502,
        )

    try:
        backend_response = response.json()
    except ValueError:
        backend_response = {"raw_text": response.text}

    backend_error_stage = None
    if isinstance(backend_response, dict):
        backend_error_stage = backend_response.get("error_stage")
        if backend_error_stage is None and isinstance(backend_response.get("detail"), dict):
            backend_error_stage = backend_response["detail"].get("error_stage")
    logger.info(
        "stage=bff_proxy_response user=%s path=%s target_url=%s backend_status=%s backend_error_stage=%s",
        username,
        path,
        target_url,
        response.status_code,
        backend_error_stage,
    )
    payload = {
        "via": "demo-bff",
        "proxy_user": username,
        "backend_url": target_url,
        "backend_status": response.status_code,
        "error_stage": backend_error_stage,
        "backend_response": backend_response,
    }
    return payload, response.status_code


async def proxy_backend_api(
    settings: Settings,
    session_info: dict[str, Any],
    path: str,
) -> JSONResponse:
    payload, status_code = await fetch_backend_api_result(settings, session_info, path)
    return build_backend_json_response(payload, status_code)
