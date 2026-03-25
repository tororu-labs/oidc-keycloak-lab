from __future__ import annotations

import os
from dataclasses import dataclass


# Backend API が token 検証で使う設定値をまとめる。
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


# 環境変数から token 検証用の設定を読み込む。
def load_settings() -> Settings:
    return Settings(
        keycloak_base_url=os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/"),
        keycloak_realm=os.getenv("KEYCLOAK_REALM", "lab"),
        jwks_cache_ttl_seconds=int(os.getenv("JWKS_CACHE_TTL_SECONDS", "300")),
        clock_skew_seconds=int(os.getenv("CLOCK_SKEW_SECONDS", "30")),
    )
