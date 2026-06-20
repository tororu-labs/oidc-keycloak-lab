from __future__ import annotations

import secrets
import time
from typing import Any


# 学習用として、メモリ上にだけ session を保持する簡易ストア。
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

    def update(self, session_id: str, payload: dict[str, Any]) -> None:
        """既存 session のデータを更新する（TTL はリセットしない）。"""
        if session_id in self._store:
            existing = self._store[session_id]
            self._store[session_id] = {
                **payload,
                "created_at": existing["created_at"],
                "expires_at": existing["expires_at"],
            }

    def find_by_keycloak_sid(self, keycloak_sid: str) -> tuple[str, dict[str, Any]] | None:
        """Keycloak の session ID (sid claim) から BFF session を検索する。"""
        for session_id, session in self._store.items():
            if session.get("keycloak_sid") == keycloak_sid:
                return session_id, session
        return None

    def delete(self, session_id: str | None) -> None:
        if session_id:
            self._store.pop(session_id, None)
