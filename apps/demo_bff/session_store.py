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

    def delete(self, session_id: str | None) -> None:
        if session_id:
            self._store.pop(session_id, None)
