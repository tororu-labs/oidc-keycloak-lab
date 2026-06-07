from __future__ import annotations

import base64
import json
import time
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from auth import build_claim_summary, build_verify_access_token, extract_roles, parse_bearer_token
from config import Settings
from fastapi import HTTPException
from joserfc import jwt
from joserfc.jwk import KeySet, RSAKey
from jwks_cache import JwksCache

# --- テスト共通定数 ---
ISSUER = "http://test-keycloak/realms/test"
AUDIENCE = "demo-api"
VALID_KID = "test-kid-1"


# --- JWT 生成ヘルパー ---


def make_valid_payload() -> dict[str, Any]:
    """デフォルトで有効な JWT payload を返す。各テストで必要な部分だけ上書きする。"""
    now = int(time.time())
    return {
        "iss": ISSUER,
        "sub": "user-test-123",
        "aud": AUDIENCE,
        "azp": "demo-bff",
        "exp": now + 300,
        "iat": now,
        "realm_access": {"roles": ["viewer"]},
    }


def make_token(rsa_key: Any, payload: dict[str, Any], *, alg: str = "RS256") -> str:
    """RSA 秘密鍵で署名した JWT 文字列を返す。

    joserfc の jwt.encode は str を返すため bytes チェック不要。
    kid は rsa_key に付与済みのものが JWT header に自動設定される。
    """
    return jwt.encode({"alg": alg}, payload, rsa_key)


def make_none_alg_token(payload: dict[str, Any]) -> str:
    """alg=none（署名なし）の JWT を手動で組み立てる。実際の署名検証ライブラリはこれを拒否すべき。"""
    header = {"alg": "none", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    return f"{header_b64}.{payload_b64}."


def tamper_payload(token: str, overrides: dict[str, Any]) -> str:
    """JWT の payload 部分を書き換えて、署名はそのまま残す（意図的に署名不一致を作る）。"""
    parts = token.split(".")
    padding = "=" * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + padding))
    payload.update(overrides)
    new_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    return f"{parts[0]}.{new_b64}.{parts[2]}"


# --- Fixtures ---


@pytest.fixture(scope="session")
def rsa_key() -> Any:
    """テスト用 RSA 鍵ペアをセッション単位で 1 回だけ生成する。

    joserfc では generate_key の第 2 引数にパラメータ dict を渡すことで kid を直接付与できる。
    """
    return RSAKey.generate_key(2048, {"kid": VALID_KID}, private=True)


@pytest.fixture(scope="session")
def public_jwks(rsa_key: Any) -> Any:
    """公開鍵のみを含む JWKS を返す（実際の Keycloak JWKS エンドポイントと同じ構成）。

    as_dict(private=False) は公開鍵コンポーネント（n, e）のみを返す。
    """
    pub_dict = rsa_key.as_dict(private=False)
    return KeySet.import_key_set({"keys": [pub_dict]})


@pytest.fixture
def primed_cache(public_jwks: Any) -> JwksCache:
    """公開鍵セットをあらかじめ格納した JwksCache を返す。HTTP 不要でテストできる。"""
    cache = JwksCache(ttl_seconds=3600)
    cache.set(public_jwks)
    return cache


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        keycloak_base_url="http://test-keycloak",
        keycloak_realm="test",
        jwks_cache_ttl_seconds=300,
        clock_skew_seconds=0,
        expected_audience=AUDIENCE,
    )


@pytest.fixture
def verify_token(test_settings: Settings, primed_cache: JwksCache) -> Any:
    """build_verify_access_token が返す async 関数を fixture として公開する。"""
    return build_verify_access_token(test_settings, primed_cache)


# ============================================================
# ユーティリティ関数のテスト
# ============================================================


def test_parse_bearer_token_missing_header():
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token(None)
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_invalid_scheme():
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token("Basic abc123")
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_missing_token_value():
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token("Bearer ")
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_valid():
    token = parse_bearer_token("Bearer mytoken.abc.xyz")
    assert token == "mytoken.abc.xyz"


def test_extract_roles_empty_claims():
    assert extract_roles({}) == []


def test_extract_roles_no_realm_access():
    assert extract_roles({"sub": "user-1"}) == []


def test_extract_roles_with_roles():
    claims = {"realm_access": {"roles": ["admin", "user"]}}
    assert extract_roles(claims) == ["admin", "user"]


def test_extract_roles_non_list_is_ignored():
    claims = {"realm_access": {"roles": "admin"}}
    assert extract_roles(claims) == []


def test_build_claim_summary_structure():
    claims = {
        "sub": "user-123",
        "preferred_username": "alice",
        "azp": "demo-client",
        "iss": "http://keycloak/realm",
        "scope": "openid profile",
        "realm_access": {"roles": ["user"]},
        "exp": 9999999,
        "iat": 1000000,
    }
    summary = build_claim_summary(claims)
    assert summary["sub"] == "user-123"
    assert summary["preferred_username"] == "alice"
    assert summary["roles"] == ["user"]
    assert summary["azp"] == "demo-client"
    assert summary["exp"] == 9999999


# ============================================================
# JWT 検証の統合テスト（異常系）
# ============================================================


async def test_valid_token(rsa_key: Any, verify_token: Any) -> None:
    """正常系: 正しい token は claims を返す。"""
    payload = make_valid_payload()
    token = make_token(rsa_key, payload)
    claims = await verify_token(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"
    assert claims["iss"] == ISSUER
    assert claims["aud"] == AUDIENCE


async def test_tampered_payload(
    rsa_key: Any, test_settings: Settings, primed_cache: JwksCache, public_jwks: Any
) -> None:
    """署名改ざん: payload を書き換えた token は BadSignatureError → 401 になる。

    BadSignatureError が発生すると auth.py はキャッシュをクリアして retry する。
    retry 時の HTTP 呼び出しを避けるため load_jwks をモックして常に同じ JWKS を返す。
    """
    payload = make_valid_payload()
    token = make_token(rsa_key, payload)
    tampered = tamper_payload(token, {"sub": "attacker-injected"})

    with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
        verify = build_verify_access_token(test_settings, primed_cache)
        with pytest.raises(HTTPException) as exc_info:
            await verify(authorization=f"Bearer {tampered}")
    assert exc_info.value.status_code == 401
    assert cast(dict[str, Any], exc_info.value.detail)["error_stage"] == "backend_authentication"


async def test_alg_none(verify_token: Any) -> None:
    """alg=none 攻撃: 署名なし token は JoseError として弾かれ 401 になる。

    Authlib はデフォルトで none アルゴリズムを登録しないため、
    キー検索に失敗して JoseError が発生する。
    """
    payload = make_valid_payload()
    none_token = make_none_alg_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {none_token}")
    assert exc_info.value.status_code == 401


async def test_token_signed_with_different_key_is_rejected(
    test_settings: Settings, primed_cache: JwksCache, public_jwks: Any
) -> None:
    """kid 不正: JWKS に存在しない kid を持つ token は BadSignatureError → 401 になる。

    joserfc は jwt.encode 時に header の kid を署名鍵の kid で自動設定する。
    JWKS に未登録の鍵で署名 → JWT の kid が JWKS にない → BadSignatureError が発生する。
    auth.py は attempt=0 で BadSignatureError → キャッシュクリアして retry する。
    retry 時の HTTP を避けるため load_jwks をモックし、同じ JWKS を返す。
    attempt=1 でも同じ kid が見つからないため、最終的に 401 になる。
    """
    # JWKS に含まれていない別鍵ペアを生成する（kid は自動的に JWT header に入る）
    other_key = RSAKey.generate_key(2048, {"kid": "attacker-key-999"}, private=True)

    payload = make_valid_payload()
    token = make_token(other_key, payload)  # kid は other_key の kid="attacker-key-999" が入る

    with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
        verify = build_verify_access_token(test_settings, primed_cache)
        with pytest.raises(HTTPException) as exc_info:
            await verify(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
    assert cast(dict[str, Any], exc_info.value.detail)["error_stage"] == "backend_authentication"


async def test_expired_token(rsa_key: Any, verify_token: Any) -> None:
    """exp 期限切れ: 有効期限が過ぎた token は ExpiredTokenError → 401 になる。"""
    payload = make_valid_payload()
    payload["exp"] = int(time.time()) - 600  # 10 分前に期限切れ
    token = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


async def test_exp_boundary_within_leeway(rsa_key: Any, primed_cache: JwksCache) -> None:
    """exp 境界（leeway 内）: leeway=30s の設定では 10 秒前期限切れでも通る。

    clock_skew_seconds は Authlib の validate(leeway=...) に渡される。
    NTP ずれや処理遅延を吸収するために使う。
    """
    settings_with_leeway = Settings(
        keycloak_base_url="http://test-keycloak",
        keycloak_realm="test",
        jwks_cache_ttl_seconds=300,
        clock_skew_seconds=30,
        expected_audience=AUDIENCE,
    )
    verify = build_verify_access_token(settings_with_leeway, primed_cache)

    payload = make_valid_payload()
    payload["exp"] = int(time.time()) - 10  # 10 秒前に期限切れ（leeway=30 秒以内）
    token = make_token(rsa_key, payload)

    claims = await verify(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"


async def test_missing_exp(rsa_key: Any, verify_token: Any) -> None:
    """exp 欠落: exp がない token は Authlib の validate() を通過する（設計上の把握ポイント）。

    RFC 7519 で exp は必須でなく、Authlib もデフォルトでは要求しない。
    この挙動を知ったうえで、必要なら claims_options に
        "exp": {"essential": True}
    を追加して必須化する。
    """
    payload = make_valid_payload()
    del payload["exp"]
    token = make_token(rsa_key, payload)

    # exp がなくても通る → 現在の auth.py の挙動を記録する
    claims = await verify_token(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"
    assert claims.get("exp") is None


async def test_wrong_audience(rsa_key: Any, verify_token: Any) -> None:
    """aud 不一致: 別サービス向けの token は InvalidClaimError → 401 になる。

    confused deputy 攻撃（別サービス向けの token を使って API にアクセスする試み）の防御。
    """
    payload = make_valid_payload()
    payload["aud"] = "other-service"  # demo-api ではない audience
    token = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


async def test_wrong_issuer(rsa_key: Any, verify_token: Any) -> None:
    """iss 不一致: 別の realm から発行された token は InvalidClaimError → 401 になる。

    iss 検証で、想定外の Keycloak realm やサードパーティが発行した token を弾く。
    """
    payload = make_valid_payload()
    payload["iss"] = "http://evil-keycloak/realms/evil"
    token = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
