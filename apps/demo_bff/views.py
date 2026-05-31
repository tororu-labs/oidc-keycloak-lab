from __future__ import annotations

import json
import time
from html import escape
from typing import Any

from fastapi.responses import HTMLResponse


class UTF8HTMLResponse(HTMLResponse):
    media_type = "text/html; charset=utf-8"


# JSON を画面に見やすく表示するための整形ヘルパー。
def format_json_block(data: dict[str, Any]) -> str:
    return escape(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


# 画面全体の共通レイアウトをまとめる。
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
    .callout.success {{
      background: #e7f6ea;
      border-color: #9fd0aa;
      color: #1f5130;
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
    return UTF8HTMLResponse(html, status_code=status_code)


# 起動に必要な設定が不足しているときの案内表示。
def configuration_issue_markup(configuration_issues: list[str]) -> str:
    if not configuration_issues:
        return ""

    items = "".join(f"<li>{escape(issue)}</li>" for issue in configuration_issues)
    return (
        '<div class="callout danger">'
        "<strong>設定が未完了です。</strong>"
        '<p class="muted">この状態でも画面は開けますが、/login は開始できません。</p>'
        f"<ul>{items}</ul>"
        "</div>"
    )


# ホーム画面は、未ログイン時とログイン済みで内容を出し分ける。
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
      <li><code>/api/me</code> と <code>/api/admin-data</code> で別 API を Bearer token 付きで呼べること</li>
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
  <a class="button secondary" href="/api/me">/api/me を開く</a>
  <a class="button secondary" href="/api/admin-data">/api/admin-data を開く</a>
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
    <code>/me</code> と <code>/admin</code> は BFF 自身の確認、
    <code>/api/me</code> と <code>/api/admin-data</code> は別 Backend API への代理呼び出しです。
  </p>
</div>
<pre>{format_json_block(session_state)}</pre>
<div class="actions">
  <a class="button" href="/me">/me を開く</a>
  <a class="button secondary" href="/admin">/admin を開く</a>
  <a class="button secondary" href="/api/me">/api/me を開く</a>
  <a class="button secondary" href="/api/admin-data">/api/admin-data を開く</a>
  <form method="post" action="/logout">
    <button class="secondary" type="submit">ログアウト</button>
  </form>
</div>
"""
    return render_page("FastAPI OIDC Demo", body)


# /me 用に、session から読める user 情報を見やすく表示する。
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
  <a class="button secondary" href="/api/me">/api/me を開く</a>
  <a class="button secondary" href="/api/admin-data">/api/admin-data を試す</a>
</div>
"""
    return render_page("/me", body)


# /admin に入れたときは、admin role を持っていることを画面で示す。
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
  <a class="button secondary" href="/api/admin-data">/api/admin-data を開く</a>
</div>
"""
    return render_page("/admin", body)


# エラー画面では、理由に加えて失敗地点も見えるようにする。
def render_error_page(
    title: str,
    message: str,
    status_code: int,
    error_stage: str | None = None,
) -> HTMLResponse:
    stage_markup = f'<p class="muted">error_stage: <code>{escape(error_stage)}</code></p>' if error_stage else ""
    body = f"""
<h1>{escape(title)}</h1>
<div class="callout danger">
  <strong>リクエストを完了できませんでした。</strong>
  {stage_markup}
  <p>{escape(message)}</p>
</div>
<div class="actions">
  <a class="button" href="/">ホームへ戻る</a>
</div>
"""
    return render_page(title, body, status_code=status_code)


def render_backend_result_page(
    title: str,
    path: str,
    payload: dict[str, Any],
    status_code: int,
) -> HTMLResponse:
    backend_status = payload.get("backend_status", status_code)
    error_stage = payload.get("error_stage") or "none"
    backend_response = payload.get("backend_response", {})
    if isinstance(backend_response, dict):
        detail = backend_response.get("detail")
        if isinstance(detail, dict):
            detail_message = detail.get("message")
            detail_stage = detail.get("error_stage")
        else:
            detail_message = detail
            detail_stage = None
        user = backend_response.get("user", {})
        message = backend_response.get("message")
    else:
        detail_message = None
        detail_stage = None
        user = {}
        message = None

    is_success = 200 <= int(status_code) < 300
    status_tone = "success" if is_success else "danger"
    status_heading = "成功" if is_success else "失敗"
    status_summary = (
        "Backend API まで到達し、期待した処理が完了している。"
        if is_success
        else "どこで止まったかを error_stage と detail から切り分ける。"
    )
    points: list[str] = [
        f"backend_status が {backend_status} か",
        f"error_stage が {error_stage} か",
        f"backend_url が {payload.get('backend_url', '(unknown)')} か",
    ]
    if user:
        points.extend(
            [
                f"preferred_username が {user.get('preferred_username', '(unknown)')} か",
                f"roles に {', '.join(user.get('roles', [])) or '(none)'} が入っているか",
                f"iss が {user.get('iss', '(unknown)')} か",
            ]
        )
    if detail_stage:
        points.append(f"backend_response.detail.error_stage が {detail_stage} か")
    if detail_message:
        points.append(f"detail.message が {detail_message} か")
    elif message:
        points.append(f"backend_response.message が {message} か")

    point_markup = "".join(f"<li>{escape(point)}</li>" for point in points)
    body = f"""
<h1>{escape(title)}</h1>
<p class="muted">
  この画面は BFF が Backend API を呼び出した結果を、読みやすい形でまとめている。
</p>
<div class="callout {status_tone}">
  <strong>判定: {status_heading}</strong>
  <p class="muted">{escape(status_summary)}</p>
</div>
<section class="card">
  <h2>今回見る値</h2>
  <p><strong>path</strong>: <code>{escape(path)}</code></p>
  <p><strong>backend_status</strong>: <code>{escape(str(backend_status))}</code></p>
  <p><strong>error_stage</strong>: <code>{escape(str(error_stage))}</code></p>
  <p><strong>proxy_user</strong>: <code>{escape(str(payload.get("proxy_user", "(unknown)")))}</code></p>
</section>
<section class="card">
  <h2>ここで見るポイント</h2>
  <ul>{point_markup}</ul>
</section>
<h2>生データ</h2>
<p class="muted">
  下の JSON は BFF が返した内容そのもの。必要なら raw JSON としても開ける。
</p>
<pre>{format_json_block(payload)}</pre>
<div class="actions">
  <a class="button" href="{escape(path)}?raw=1">raw JSON を開く</a>
  <a class="button secondary" href="/">ホームへ戻る</a>
  <a class="button secondary" href="/me">/me を開く</a>
  <a class="button secondary" href="/admin">/admin を開く</a>
</div>
"""
    return render_page(title, body, status_code=status_code)
