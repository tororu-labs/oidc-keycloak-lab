from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlencode

from auth import build_user_summary, decode_jwt_payload, sanitize_next_path
from authlib.integrations.starlette_client import OAuth, OAuthError
from backend_api import build_backend_json_response, fetch_backend_api_result
from config import load_settings
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from session_store import InMemorySessionStore
from starlette.middleware.sessions import SessionMiddleware
from views import (
    render_admin_page,
    render_backend_result_page,
    render_error_page,
    render_home,
    render_profile_page,
)

logger = logging.getLogger("uvicorn.error")

# 起動時に設定を読み込み、開発用の insecure transport もここで許可する。
settings, configuration_issues = load_settings()

if settings.keycloak_base_url.startswith("http://") or settings.app_base_url.startswith("http://"):
    os.environ.setdefault("AUTHLIB_INSECURE_TRANSPORT", "1")

app = FastAPI(title="FastAPI OIDC Demo")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.session_cookie_name,
    same_site="lax",
    https_only=False,
)
app.state.configuration_issues = configuration_issues
app.state.session_store = InMemorySessionStore(settings.session_ttl_seconds)

oauth = OAuth()
oauth.register(
    name="keycloak",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.discovery_url,
    client_kwargs={"scope": settings.scope},
)
app.state.oauth = oauth


# Cookie 内の session ID から、現在のログイン情報を復元する。
def get_active_session(request: Request) -> dict[str, Any] | None:
    session_id = request.session.get("sid")
    session_info = app.state.session_store.get(session_id)
    if session_info is None and session_id:
        request.session.clear()
    return session_info


# ここから下は BFF の画面と認証フローを受け持つ route 群。
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    session_info = get_active_session(request)
    user = session_info["user"] if session_info else None
    return render_home(user, app.state.configuration_issues, session_info)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    if app.state.configuration_issues:
        message = " / ".join(app.state.configuration_issues)
        logger.warning("stage=bff_login_configuration_error issues=%s", message)
        return render_error_page("設定不足", message, 500, error_stage="bff_configuration")

    next_path = sanitize_next_path(request.query_params.get("next"))
    request.session["after_login_path"] = next_path
    logger.info("stage=bff_login_start next_path=%s", next_path)
    return await app.state.oauth.keycloak.authorize_redirect(
        request,
        settings.authorization_callback_url,
    )


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    try:
        token = await app.state.oauth.keycloak.authorize_access_token(request)
    except OAuthError as exc:
        message = f"Keycloak との認可処理に失敗しました。 error={exc.error!r}, description={exc.description!r}"
        logger.warning(
            "stage=bff_callback_error error=%s description=%s",
            exc.error,
            exc.description,
        )
        return render_error_page("OIDC callback エラー", message, 400, error_stage="callback")
    except Exception as exc:  # pragma: no cover - integration failure path
        message = (
            "Keycloak から token を取得できませんでした。"
            " Keycloak が停止している、client secret が違う、"
            " redirect URI が一致していない可能性があります。"
            f" detail={exc}"
        )
        logger.warning("stage=bff_token_exchange_error detail=%s", str(exc))
        return render_error_page(
            "Token 交換エラー",
            message,
            502,
            error_stage="token_exchange",
        )

    previous_session_id = request.session.get("sid")
    app.state.session_store.delete(previous_session_id)

    access_claims = decode_jwt_payload(token.get("access_token"))
    id_claims = decode_jwt_payload(token.get("id_token"))
    user = build_user_summary(access_claims, id_claims)

    session_payload = {
        "access_token": token.get("access_token"),
        "id_token": token.get("id_token"),
        "user": user,
        "access_claims": access_claims,
        "id_claims": id_claims,
    }
    request.session["sid"] = app.state.session_store.create(session_payload)
    next_path = sanitize_next_path(request.session.pop("after_login_path", "/me"))
    logger.info(
        "stage=bff_callback_success user=%s roles=%s iss=%s next_path=%s",
        user["preferred_username"],
        user["roles"],
        user["issuer"],
        next_path,
    )
    return RedirectResponse(next_path, status_code=303)


@app.get("/me", response_class=HTMLResponse)
async def me(request: Request):
    session_info = get_active_session(request)
    if session_info is None:
        return RedirectResponse("/login?next=/me", status_code=303)
    return render_profile_page(session_info)


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    session_info = get_active_session(request)
    if session_info is None:
        return RedirectResponse("/login?next=/admin", status_code=303)

    roles = session_info["user"]["roles"]
    if "admin" not in roles:
        message = (
            f"{session_info['user']['preferred_username']} は admin role を持っていないため、"
            " /admin へはアクセスできません。"
        )
        logger.info(
            "stage=bff_authorization_error user=%s roles=%s required_role=admin",
            session_info["user"]["preferred_username"],
            roles,
        )
        return render_error_page(
            "403 Forbidden",
            message,
            403,
            error_stage="bff_authorization",
        )
    return render_admin_page(session_info)


@app.get("/api/me", response_model=None)
async def api_me(request: Request) -> JSONResponse | RedirectResponse | HTMLResponse:
    session_info = get_active_session(request)
    if session_info is None:
        return RedirectResponse("/login?next=/api/me", status_code=303)
    payload, status_code = await fetch_backend_api_result(settings, session_info, "/me")
    if request.query_params.get("raw") == "1":
        return build_backend_json_response(payload, status_code)
    return render_backend_result_page("/api/me", "/api/me", payload, status_code)


@app.get("/api/admin-data", response_model=None)
async def api_admin_data(request: Request) -> JSONResponse | RedirectResponse | HTMLResponse:
    session_info = get_active_session(request)
    if session_info is None:
        return RedirectResponse("/login?next=/api/admin-data", status_code=303)
    payload, status_code = await fetch_backend_api_result(settings, session_info, "/admin-data")
    if request.query_params.get("raw") == "1":
        return build_backend_json_response(payload, status_code)
    return render_backend_result_page("/api/admin-data", "/api/admin-data", payload, status_code)


@app.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    session_info = get_active_session(request)
    session_id = request.session.get("sid")
    app.state.session_store.delete(session_id)
    request.session.clear()

    params = {"post_logout_redirect_uri": settings.logout_redirect_url}
    if session_info and session_info.get("id_token"):
        params["id_token_hint"] = session_info["id_token"]

    logout_url = f"{settings.logout_endpoint}?{urlencode(params)}"
    return RedirectResponse(logout_url, status_code=303)
