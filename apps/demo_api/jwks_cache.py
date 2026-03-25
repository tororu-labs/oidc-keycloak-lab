from __future__ import annotations

import time
from typing import Any


# Keycloak の公開鍵取得結果を、短時間だけ再利用する簡易キャッシュ。
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
