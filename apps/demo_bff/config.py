from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_SESSION_SECRET = "change-this-session-secret"
DEFAULT_CLIENT_SECRET = "change-this-client-secret"


# BFF 全体で使う設定値を 1 つにまとめる。
@dataclass(frozen=True)
class Settings:
    keycloak_base_url: str
    keycloak_realm: str
    oidc_client_id: str
    oidc_client_secret: str
    app_base_url: str
    backend_api_base_url: str
    backend_api_timeout_seconds: float
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


# 環境変数から設定を読み込み、未設定もここでまとめて確認する。
def load_settings() -> tuple[Settings, list[str]]:
    keycloak_base_url = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")
    app_base_url = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    backend_api_base_url = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8001").rstrip("/")
    oidc_client_secret = os.getenv("OIDC_CLIENT_SECRET", DEFAULT_CLIENT_SECRET)
    session_secret = os.getenv("SESSION_SECRET", DEFAULT_SESSION_SECRET)

    settings = Settings(
        keycloak_base_url=keycloak_base_url,
        keycloak_realm=os.getenv("KEYCLOAK_REALM", "lab"),
        oidc_client_id=os.getenv("OIDC_CLIENT_ID", "demo-bff"),
        oidc_client_secret=oidc_client_secret,
        app_base_url=app_base_url,
        backend_api_base_url=backend_api_base_url,
        backend_api_timeout_seconds=float(os.getenv("BACKEND_API_TIMEOUT_SECONDS", "5")),
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
        configuration_issues.append("SESSION_SECRET が未設定です。Cookie 署名用のランダム文字列を設定してください。")
    return settings, configuration_issues
