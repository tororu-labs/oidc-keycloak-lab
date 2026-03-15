from __future__ import annotations

import base64
import json
import os
import secrets
import time
from dataclasses import dataclass
from html import escape
from typing import Any
from urllib.parse import urlencode, urlparse

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware


DEFAULT_SESSION_SECRET = "change-this-session-secret"
DEFAULT_CLIENT_SECRET = "change-this-client-secret"


@dataclass(frozen=True)
class Settings:
    keycloak_base_url: str
    keycloak_realm: str
    oidc_client_id: str
    oidc_client_secret: str
    app_base_url: str
    session_secret: str
    session_cookie_name: str
    session_ttl_seconds: int
    scope: str

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_base_url}/realms/{self.keycloak_realm}"

    @property
    def discovery_url(self) -> str:
        return f"{self.issuer}/.well-known/openid-configuration"

    @property
    def authorization_callback_url(self) -> str:
        return f"{self.app_base_url}/auth/callback"

    @property
    def logout_redirect_url(self) -> str:
        return f"{self.app_base_url}/"

    @property
    def logout_endpoint(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/logout"


class InMemorySessionStore:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}

    def create(self, payload: dict[str, Any]) -> str:
        now = time.time()
        session_id = secrets.token_urlsafe(32)
        self._store[session_id] = {
            **payload,
            "created_at": now,
            "expires_at": now + self.ttl_seconds,
        }
        return session_id

    def get(self, session_id: str | None) -> dict[str, Any] | None:
        if not session_id:
            return None

        session = self._store.get(session_id)
        if session is None:
            return None

        if session["expires_at"] <= time.time():
            self.delete(session_id)
            return None

        session["expires_at"] = time.time() + self.ttl_seconds
        return session

    def delete(self, session_id: str | None) -> None:
        if session_id:
            self._store.pop(session_id, None)


def load_settings() -> tuple[Settings, list[str]]:
    keycloak_base_url = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")
    app_base_url = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    oidc_client_secret = os.getenv("OIDC_CLIENT_SECRET", DEFAULT_CLIENT_SECRET)
    session_secret = os.getenv("SESSION_SECRET", DEFAULT_SESSION_SECRET)

    settings = Settings(
        keycloak_base_url=keycloak_base_url,
        keycloak_realm=os.getenv("KEYCLOAK_REALM", "lab"),
        oidc_client_id=os.getenv("OIDC_CLIENT_ID", "demo-bff"),
        oidc_client_secret=oidc_client_secret,
        app_base_url=app_base_url,
        session_secret=session_secret,
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "demo_bff"),
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "3600")),
        scope=os.getenv("OIDC_SCOPE", "openid profile email"),
    )

    configuration_issues: list[str] = []
    if oidc_client_secret == DEFAULT_CLIENT_SECRET:
        configuration_issues.append(
            "OIDC_CLIENT_SECRET が未設定です。Keycloak の demo-bff client secret を設定してください。"
        )
    if session_secret == DEFAULT_SESSION_SECRET:
        configuration_issues.append(
            "SESSION_SECRET が未設定です。Cookie 署名用のランダム文字列を設定してください。"
        )
    return settings, configuration_issues


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


def sanitize_next_path(candidate: str | None) -> str:
    if not candidate:
        return "/me"
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return "/me"
    if not candidate.startswith("/"):
        return "/me"
    return candidate


def format_json_block(data: dict[str, Any]) -> str:
    return escape(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def render_page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffaf1;
      --ink: #1b1f1f;
      --muted: #5e625f;
      --accent: #14532d;
      --accent-soft: #d7ead8;
      --danger: #8a1c1c;
      --border: #d8cdb8;
      --code: #f0eadc;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #f8f2c8 0%, transparent 28%),
        linear-gradient(180deg, #f7f2e9 0%, var(--bg) 100%);
    }}
    main {{
      max-width: 920px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 20px 35px rgba(74, 58, 33, 0.08);
    }}
    h1, h2 {{
      margin-top: 0;
      font-family: Georgia, "Times New Roman", serif;
      letter-spacing: 0.01em;
    }}
    p, li {{
      line-height: 1.7;
    }}
    .muted {{
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 14px;
      margin: 20px 0;
    }}
    .card {{
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 20px;
    }}
    a.button, button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 0 18px;
      border-radius: 999px;
      border: 1px solid var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
    }}
    a.button.secondary, button.secondary {{
      background: transparent;
      color: var(--accent);
    }}
    form {{
      margin: 0;
    }}
    .callout {{
      margin: 18px 0;
      padding: 14px 16px;
      border-radius: 12px;
      background: var(--accent-soft);
      border: 1px solid #b6d2b8;
    }}
    .callout.danger {{
      background: #fde8e8;
      border-color: #f5b5b5;
      color: var(--danger);
    }}
    code, pre {{
      font-family: "SFMono-Regular", Menlo, Consolas, monospace;
      background: var(--code);
    }}
    code {{
      padding: 2px 6px;
      border-radius: 6px;
    }}
    pre {{
      padding: 16px;
      border-radius: 14px;
      overflow-x: auto;
      border: 1px solid var(--border);
    }}
    ul {{
      padding-left: 18px;
    }}
  </style>
</head>
<body>
  <main>
    <div class="panel">
      {body}
    </div>
  </main>
</body>
</html>
"""
    return HTMLResponse(html, status_code=status_code)


def configuration_issue_markup(configuration_issues: list[str]) -> str:
    if not configuration_issues:
        return ""

    items = "".join(f"<li>{escape(issue)}</li>" for issue in configuration_issues)
    return (
        '<div class="callout danger">'
        "<strong>設定が未完了です。</strong>"
        "<p class=\"muted\">この状態でも画面は開けますが、/login は開始できません。</p>"
        f"<ul>{items}</ul>"
        "</div>"
    )


def render_home(
    user: dict[str, Any] | None,
    configuration_issues: list[str],
    session_info: dict[str, Any] | None,
) -> HTMLResponse:
    issue_block = configuration_issue_markup(configuration_issues)
    if user is None:
        body = f"""
<h1>FastAPI x Keycloak 最小 OIDC ハンズオン</h1>
<p class="muted">
  このアプリは、Keycloak で作成した <code>realm / user / role / client</code> を
  実際の Web アプリから使うための最小検証用 BFF です。
</p>
{issue_block}
<div class="grid">
  <section class="card">
    <h2>このアプリで確認すること</h2>
    <ul>
      <li>Keycloak にリダイレクトしてログインできること</li>
      <li>Callback で token を受け取り session を作ること</li>
      <li><code>/me</code> で user 情報と role を見られること</li>
      <li><code>/admin</code> で <code>admin</code> role を判定できること</li>
    </ul>
  </section>
  <section class="card">
    <h2>想定ユーザー</h2>
    <ul>
      <li><code>alice</code>: <code>viewer</code> role</li>
      <li><code>bob</code>: <code>admin</code> role</li>
    </ul>
  </section>
</div>
<div class="actions">
  <a class="button" href="/login">Keycloak でログイン</a>
  <a class="button secondary" href="/me">/me を開く</a>
  <a class="button secondary" href="/admin">/admin を開く</a>
</div>
"""
        return render_page("FastAPI OIDC Demo", body)

    session_state = {
        "preferred_username": user["preferred_username"],
        "roles": user["roles"],
        "session_expires_at": time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(session_info["expires_at"]),
        )
        if session_info
        else None,
    }
    body = f"""
<h1>ログイン済みです</h1>
<p class="muted">
  FastAPI が Keycloak から受け取った認証結果を session として保持し、
  以後のリクエストでは Cookie からログイン状態を復元しています。
</p>
<div class="grid">
  <section class="card">
    <h2>現在のユーザー</h2>
    <p><strong>{escape(user["preferred_username"])}</strong></p>
    <p class="muted">sub: <code>{escape(user["sub"] or "unknown")}</code></p>
  </section>
  <section class="card">
    <h2>現在の role</h2>
    <p><code>{escape(", ".join(user["roles"]) or "(none)")}</code></p>
  </section>
</div>
<div class="callout">
  <strong>次に見ると理解しやすいポイント</strong>
  <p class="muted">
    <code>/me</code> で claims を確認し、<code>/admin</code> で role 判定の結果を見比べてください。
  </p>
</div>
<pre>{format_json_block(session_state)}</pre>
<div class="actions">
  <a class="button" href="/me">/me を開く</a>
  <a class="button secondary" href="/admin">/admin を開く</a>
  <form method="post" action="/logout">
    <button class="secondary" type="submit">ログアウト</button>
  </form>
</div>
"""
    return render_page("FastAPI OIDC Demo", body)


def render_profile_page(session_info: dict[str, Any]) -> HTMLResponse:
    user = session_info["user"]
    claims_view = {
        "sub": user["sub"],
        "preferred_username": user["preferred_username"],
        "roles": user["roles"],
        "iss": user["issuer"],
        "scope": user["scope"],
        "session_expires_at": time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(session_info["expires_at"]),
        ),
    }
    body = f"""
<h1>/me</h1>
<p class="muted">
  このページは FastAPI が保持している session から user 情報を取り出し、
  Access Token の claims を読みやすい形で表示しています。
</p>
<pre>{format_json_block(claims_view)}</pre>
<div class="actions">
  <a class="button" href="/">ホームへ戻る</a>
  <a class="button secondary" href="/admin">/admin を試す</a>
</div>
"""
    return render_page("/me", body)


def render_admin_page(session_info: dict[str, Any]) -> HTMLResponse:
    user = session_info["user"]
    body = f"""
<h1>/admin</h1>
<div class="callout">
  <strong>admin role を確認できました。</strong>
  <p class="muted">
    <code>{escape(user["preferred_username"])}</code> は
    <code>admin</code> を持っているため、このページに到達できています。
  </p>
</div>
<pre>{format_json_block(user)}</pre>
<div class="actions">
  <a class="button" href="/">ホームへ戻る</a>
  <a class="button secondary" href="/me">/me を開く</a>
</div>
"""
    return render_page("/admin", body)


def render_error_page(title: str, message: str, status_code: int) -> HTMLResponse:
    body = f"""
<h1>{escape(title)}</h1>
<div class="callout danger">
  <strong>リクエストを完了できませんでした。</strong>
  <p>{escape(message)}</p>
</div>
<div class="actions">
  <a class="button" href="/">ホームへ戻る</a>
</div>
"""
    return render_page(title, body, status_code=status_code)


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


def get_active_session(request: Request) -> dict[str, Any] | None:
    session_id = request.session.get("sid")
    session_info = app.state.session_store.get(session_id)
    if session_info is None and session_id:
        request.session.clear()
    return session_info


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    session_info = get_active_session(request)
    user = session_info["user"] if session_info else None
    return render_home(user, app.state.configuration_issues, session_info)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    if app.state.configuration_issues:
        message = " / ".join(app.state.configuration_issues)
        return render_error_page("設定不足", message, 500)

    next_path = sanitize_next_path(request.query_params.get("next"))
    request.session["after_login_path"] = next_path
    return await app.state.oauth.keycloak.authorize_redirect(
        request,
        settings.authorization_callback_url,
    )


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    try:
        token = await app.state.oauth.keycloak.authorize_access_token(request)
    except OAuthError as exc:
        message = (
            "Keycloak との認可処理に失敗しました。"
            f" error={exc.error!r}, description={exc.description!r}"
        )
        return render_error_page("OIDC callback エラー", message, 400)
    except Exception as exc:  # pragma: no cover - integration failure path
        message = (
            "Keycloak から token を取得できませんでした。"
            " Keycloak が停止している、client secret が違う、"
            " redirect URI が一致していない可能性があります。"
            f" detail={exc}"
        )
        return render_error_page("Token 交換エラー", message, 502)

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
        return render_error_page("403 Forbidden", message, 403)
    return render_admin_page(session_info)


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
