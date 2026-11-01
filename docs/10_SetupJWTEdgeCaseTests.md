# Setup JWT エッジケーステスト

## ここでのゴール

この手順では、`docs/08_SetupAudienceValidation.md` まで実装した JWT 検証ロジックを pytest で体系的に検証し、次の状態に到達することをゴールとする。

- Keycloak を起動せずに、テスト用の偽の JWT を作って検証できる
- 署名改ざん・`alg=none` 攻撃・`aud` 不一致・`iss` 不一致・`exp` 境界など、異常な JWT を渡したときに API が 401 を返すことを確認できる
- 「ライブラリが自動で守ってくれる部分」と「自分のコードが責任を持つ部分」の境界を把握できる
- `pytest tests/` を実行してすべてのテストが green になる

用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。  
pytest・fixture・patch の基本は [07_PytestAndMockBasics.md](./Reference/07_PytestAndMockBasics.md) を参照する。  
claim の意味・検証順序・例外型の詳細は [05_TokenClaimsAndValidation.md](./Reference/05_TokenClaimsAndValidation.md) を参照する。

------

## この手順では深く追わなくてよいこと

この手順はセキュリティの学習 lab であるため、次の項目は「動作を知る」だけでよく、仕組みを深く追う必要はない。

- **RSA 鍵の数学的な仕組み**（鍵長・素因数分解・鍵生成アルゴリズムなど）  
  → 「RSA 2048 ビットで秘密鍵と公開鍵のペアを作る」という操作ができれば十分
- **Python の型ヒント**（`Any`・`dict[str, Any]`・`-> None` など）  
  → 型チェッカー向けの注釈であり、プログラムの動作には影響しない。読み飛ばして問題ない
- **pytest の内部動作・fixture の解決の仕組み**  
  → 「引数に書いた名前と同じ fixture が自動で注入される」という使い方だけ押さえる
- **joserfc ライブラリの内部実装**  
  → 「どの関数を呼ぶと何が返ってくるか」だけ知っていれば十分

------

## この手順で学ぶセキュリティの考え方

JWT 検証の実装が終わったとき、「動く」だけでは不十分である。悪意ある利用者がどのような方法で API を突破しようとするかを想定し、それぞれの攻撃が確かに弾かれることを確認する必要がある。

この手順では、次の 3 種類の攻撃シナリオを pytest で再現する。

| 攻撃の種類 | 具体的な手口 | 対応するテスト |
|---|---|---|
| **署名改ざん** | JWT のペイロードだけ書き換えて、署名はそのまま残す | `test_tampered_payload` |
| **偽造（偽鍵なりすまし）** | 攻撃者が自分で生成した秘密鍵で JWT を作り、正規の Keycloak が発行したように見せかける | `test_token_signed_with_different_key_is_rejected` |
| **署名スキップ（alg=none 攻撃）** | `alg=none` と書いた JWT を作り、署名なしで通過しようとする | `test_alg_none` |
| **なりすまし（confused deputy）** | 別のサービス宛てや別の認証サーバーが発行した JWT を使い回す | `test_wrong_audience`・`test_wrong_issuer` |

テストを書く目的は「バグを見つけること」だけではない。「この攻撃が届かないことを確認し、将来も保証し続けること」がもう一つの目的である。

------

## 前提確認

この手順を始める前に、以下が完了していることを確認する。

- `docs/08_SetupAudienceValidation.md` の手順が完了している
- `apps/demo_api/` の Python 仮想環境がセットアップされている

判定:

- `apps/demo_api/` で `pytest tests/` を実行したとき、既存のテストが通る

------

## この手順の流れ

1. asyncio の設定を確認する
2. JWT の 3 パーツを確認する
3. `tests/test_auth.py` に import・定数・ヘルパー関数を書く
4. fixture を書く
5. ユーティリティ関数テストを書いて実行する
6. JWT 検証テスト（正常系・署名系・claim 系）を書いて実行する
7. 失敗例を確認する

------

## asyncio の設定を確認する

`verify_access_token` は非同期関数であるため、`pytest-asyncio` が必要になる。  
リポジトリルートの `pyproject.toml` に以下の設定が入っていることを確認する。

~~~toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
~~~

この設定により、`async def test_xxx()` と書いた関数を `@pytest.mark.asyncio` なしで実行できる。

判定:

- `pytest tests/` を実行したとき、出力の先頭付近に `asyncio: mode=Mode.AUTO` が表示される

------

## JWT の 3 パーツを確認する

コードを書く前に、JWT がどのような形をしているかを確認しておく。  
JWT は `.` で区切られた 3 つのパーツから成る。

~~~
eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2lkLTEifQ          ← ① ヘッダー
.
eyJpc3MiOiJodHRwOi8vdGVzdC1rZXljbG9hay9yZWFsbXMvdGVzdCIs  ← ② ペイロード
.
MEUCIQD...                                                  ← ③ 署名
~~~

各パーツは Base64URL というエンコード形式で書かれているが、デコードするとただのテキストである。

| パーツ | 中身 | テストとの関係 |
|---|---|---|
| ① ヘッダー | 署名アルゴリズム（`alg`）と鍵 ID（`kid`） | `test_alg_none`・`test_token_signed_with_different_key_is_rejected` で操作する |
| ② ペイロード | `iss`・`sub`・`aud`・`exp` などの claim | `test_tampered_payload`・`test_wrong_audience` などで書き換える |
| ③ 署名 | ヘッダーとペイロードを秘密鍵で署名した値 | 署名と中身が一致しないと `BadSignatureError` になる |

署名改ざんテスト（`test_tampered_payload`）では、② のペイロードだけ書き換えて ③ の署名はそのまま残すことで、意図的に「署名と中身が一致しない JWT」を作る。これを API が 401 で弾くことを確認する。

------

## このセクションで触るファイル

この手順では `apps/demo_api/tests/test_auth.py` を 1 ファイルだけ作成する。  
fixture・ヘルパー関数・テストケースをすべてこのファイルにまとめる。

~~~
apps/demo_api/
├── conftest.py          ← 変更なし（sys.path 設定のみ）
├── auth.py              ← 変更なし（テスト対象）
├── config.py            ← 変更なし（Settings クラスを使う）
├── jwks_cache.py        ← 変更なし（JwksCache を使う）
└── tests/
    └── test_auth.py     ← ここを作る
~~~

------

## Step 1: import と共通定数

`tests/test_auth.py` を作成し、以下を先頭に書く。

~~~python
from __future__ import annotations

import base64
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
from auth import build_claim_summary, build_verify_access_token, extract_roles, parse_bearer_token
from config import Settings
from fastapi import HTTPException
from joserfc import jwt
from joserfc.jwk import KeySet, RSAKey
from jwks_cache import JwksCache

# テスト全体で使う定数
ISSUER    = "http://test-keycloak/realms/test"
AUDIENCE  = "demo-api"
VALID_KID = "test-kid-1"
~~~

各 import の役割:

| import | 何のために使うか |
|---|---|
| `base64`, `json` | `alg=none` トークンの手動組み立てに使う |
| `time` | `exp`（有効期限）を現在時刻から計算するために使う |
| `AsyncMock`, `patch` | Keycloak への HTTP 呼び出しを偽物に差し替えるために使う |
| `joserfc.jwk.RSAKey` | テスト用の RSA 鍵ペアを生成するために使う |
| `joserfc.jwk.KeySet` | 公開鍵を JWKS 形式にまとめるために使う |

`from __future__ import annotations` は Python の型ヒントを将来の書き方に統一するための設定で、動作には影響しない。

------

## Step 2: JWT 生成ヘルパー関数

この手順では、テストの中で JWT を自分で生成する必要がある。なぜなら、Keycloak を起動しなくてもテストを完結させたいからである。

定数の下に 4 つのヘルパー関数を追加する。

~~~python
def make_valid_payload() -> dict:
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


def make_token(rsa_key, payload: dict, *, alg: str = "RS256") -> str:
    """RSA 秘密鍵で署名した JWT 文字列を返す。"""
    return jwt.encode({"alg": alg}, payload, rsa_key)


def make_none_alg_token(payload: dict) -> str:
    """alg=none（署名なし）の JWT を手動で組み立てる。署名検証ライブラリはこれを拒否すべき。"""
    header = {"alg": "none", "typ": "JWT"}
    header_b64  = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    return f"{header_b64}.{payload_b64}."


def tamper_payload(token: str, overrides: dict) -> str:
    """JWT の payload 部分だけ書き換えて、署名はそのまま残す（意図的に署名不一致を作る）。"""
    parts   = token.split(".")
    # Base64URL のパディング補正。JWT はパディングを省略しているため補う。
    padding = "=" * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + padding))
    payload.update(overrides)
    new_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    return f"{parts[0]}.{new_b64}.{parts[2]}"
~~~

各関数の役割:

| 関数 | 何をするか | どのテストで使うか |
|---|---|---|
| `make_valid_payload()` | 正常な claim のセットを作る | すべてのテストの出発点 |
| `make_token()` | 秘密鍵で署名した JWT 文字列を作る | 正常系・異常系共通 |
| `make_none_alg_token()` | 署名なしの JWT を手動で組み立てる | `test_alg_none` |
| `tamper_payload()` | ペイロードだけ書き換えた（署名と不一致な）JWT を作る | `test_tampered_payload` |

------

## Step 3: fixture の定義

fixture の基本は [07_PytestAndMockBasics.md](./Reference/07_PytestAndMockBasics.md) を参照する。

このテストで使う fixture の依存関係を先に整理しておく。

~~~
rsa_key          ← RSA 鍵ペアを生成（テスト全体で 1 回）
  └─ public_jwks ← 公開鍵を JWKS 形式に変換
       └─ primed_cache ← JWKS をキャッシュに格納（Keycloak への HTTP が走らなくなる）

test_settings    ← テスト用の設定値（単独で使う）

verify_token     ← test_settings + primed_cache を組み合わせた JWT 検証関数
~~~

ヘルパー関数の下に以下を追加する。

~~~python
@pytest.fixture(scope="session")
def rsa_key():
    """テスト用 RSA 鍵ペアをセッション単位で 1 回だけ生成する。
    scope="session" により全テストで使い回す。RSA 鍵生成は計算コストが高いため毎回生成しない。
    """
    return RSAKey.generate_key(2048, {"kid": VALID_KID}, private=True)


@pytest.fixture(scope="session")
def public_jwks(rsa_key):
    """公開鍵のみを含む JWKS を返す（実際の Keycloak JWKS エンドポイントと同じ構成）。
    as_dict(private=False) は公開鍵コンポーネント（n, e）だけを返す。
    """
    pub_dict = rsa_key.as_dict(private=False)
    return KeySet.import_key_set({"keys": [pub_dict]})


@pytest.fixture
def primed_cache(public_jwks):
    """公開鍵セットをあらかじめ格納した JwksCache を返す。
    キャッシュに鍵が入っているため、テスト中に Keycloak への HTTP が走らない。
    """
    cache = JwksCache(ttl_seconds=3600)
    cache.set(public_jwks)
    return cache


@pytest.fixture
def test_settings():
    """テスト用 Settings を返す。clock_skew_seconds=0 で leeway なし（厳格な検証）。"""
    return Settings(
        keycloak_base_url="http://test-keycloak",
        keycloak_realm="test",
        jwks_cache_ttl_seconds=300,
        clock_skew_seconds=0,
        expected_audience=AUDIENCE,
    )


@pytest.fixture
def verify_token(test_settings, primed_cache):
    """build_verify_access_token が返す async 関数を fixture として公開する。
    各テストでこの fixture を引数に取るだけで JWT 検証関数を使える。
    """
    return build_verify_access_token(test_settings, primed_cache)
~~~

判定:

~~~zsh
cd apps/demo_api
pytest tests/ --collect-only
~~~

- エラーなく fixture と test の一覧が表示される

------

## Step 4: ユーティリティ関数テスト

`parse_bearer_token`・`extract_roles`・`build_claim_summary` は同期関数なので、`async def` 不要のシンプルなテストになる。

~~~python
# ============================================================
# ユーティリティ関数のテスト
# ============================================================

def test_parse_bearer_token_missing_header():
    """Authorization ヘッダーがない場合は 401 になる。"""
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token(None)
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_invalid_scheme():
    """Bearer でないスキーム（Basic など）は 401 になる。"""
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token("Basic abc123")
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_missing_token_value():
    """Bearer の後にトークン文字列がない場合は 401 になる。"""
    with pytest.raises(HTTPException) as exc_info:
        parse_bearer_token("Bearer ")
    assert exc_info.value.status_code == 401


def test_parse_bearer_token_valid():
    """正常な Bearer トークンはトークン文字列だけを返す。"""
    token = parse_bearer_token("Bearer mytoken.abc.xyz")
    assert token == "mytoken.abc.xyz"


def test_extract_roles_empty_claims():
    """claim が空の場合はロール一覧として空リストを返す。"""
    assert extract_roles({}) == []


def test_extract_roles_no_realm_access():
    """realm_access キーがない場合は空リストを返す。"""
    assert extract_roles({"sub": "user-1"}) == []


def test_extract_roles_with_roles():
    """realm_access.roles にロールがあれば一覧を返す。"""
    claims = {"realm_access": {"roles": ["admin", "user"]}}
    assert extract_roles(claims) == ["admin", "user"]


def test_extract_roles_non_list_is_ignored():
    """roles がリストでない場合（文字列など）は空リストを返す。"""
    claims = {"realm_access": {"roles": "admin"}}
    assert extract_roles(claims) == []


def test_build_claim_summary_structure():
    """build_claim_summary が期待するキーを持つ dict を返す。"""
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
    assert summary["sub"]                == "user-123"
    assert summary["preferred_username"] == "alice"
    assert summary["roles"]              == ["user"]
    assert summary["azp"]                == "demo-client"
    assert summary["exp"]                == 9999999
~~~

判定:

~~~zsh
cd apps/demo_api
pytest tests/ -v
~~~

- `test_parse_bearer_token_*`・`test_extract_roles_*`・`test_build_claim_summary_*` がすべて `PASSED`

------

## Step 5: JWT 検証テスト

### 正常系

まず「正しい JWT を渡したときに claim が返ること」を確認する。

~~~python
# ============================================================
# JWT 検証の統合テスト
# ============================================================

async def test_valid_token(rsa_key, verify_token) -> None:
    """正常系: 正しい token は claims を返す。"""
    payload = make_valid_payload()
    token   = make_token(rsa_key, payload)
    claims  = await verify_token(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"
    assert claims["iss"] == ISSUER
    assert claims["aud"] == AUDIENCE
~~~

判定:

- `claims["iss"]` が `ISSUER`、`claims["aud"]` が `AUDIENCE` と一致する

---

### 署名改ざん（BadSignatureError）

**攻撃シナリオ**: 攻撃者が他人の JWT を入手し、ペイロードの `sub`（ユーザー ID）を自分の ID に書き換えてそのまま送りつける。署名はそのままなので、署名と中身が食い違った状態になる。

**`patch` が必要な理由**:

`BadSignatureError` が発生すると `auth.py` は「鍵がローテーションされたかもしれない」と判断し、Keycloak に JWKS を再取得しに行く（retry）。テスト環境には Keycloak がないため、そのままでは 503 エラーになってしまう。

~~~
patch なしの場合:
  BadSignatureError → cache.clear() → Keycloak に HTTP → 接続失敗 → 503

patch した場合:
  BadSignatureError → cache.clear() → 偽の load_jwks → 同じ JWKS を返す
                   → 2 回目も BadSignatureError → 401
~~~

~~~python
async def test_tampered_payload(
    rsa_key, test_settings: Settings, primed_cache: JwksCache, public_jwks
) -> None:
    """署名改ざん: payload を書き換えた token は BadSignatureError → 401 になる。

    BadSignatureError 発生時に auth.py はキャッシュをクリアして retry する。
    retry 時の HTTP 呼び出しを避けるため load_jwks をモックして常に同じ JWKS を返す。
    """
    payload  = make_valid_payload()
    token    = make_token(rsa_key, payload)
    tampered = tamper_payload(token, {"sub": "attacker-injected"})

    with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
        verify = build_verify_access_token(test_settings, primed_cache)
        with pytest.raises(HTTPException) as exc_info:
            await verify(authorization=f"Bearer {tampered}")
    assert exc_info.value.status_code == 401
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["error_stage"] == "backend_authentication"
~~~

---

### alg=none 攻撃（JoseError）

**攻撃シナリオ**: JWT のヘッダーを `{"alg": "none"}` にすることで、署名検証をスキップさせようとする古典的な攻撃。

joserfc はデフォルトで `none` アルゴリズムを受け付けないため、デコード時に `JoseError` が発生する。`BadSignatureError` とは異なり retry が走らないため `patch` は不要。

~~~python
async def test_alg_none(verify_token) -> None:
    """alg=none 攻撃: 署名なし token は JoseError として弾かれ 401 になる。

    joserfc はデフォルトで none アルゴリズムを受け付けないため、
    デコード時に JoseError が発生する。
    """
    payload    = make_valid_payload()
    none_token = make_none_alg_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {none_token}")
    assert exc_info.value.status_code == 401
~~~

---

### 未知の kid（BadSignatureError）

**攻撃シナリオ**: 攻撃者が自分で用意した秘密鍵で JWT を作り、まるで正規の Keycloak が発行したかのように見せかけて送る。JWT の `kid` が JWKS に存在しないため検証に失敗する。

~~~python
async def test_token_signed_with_different_key_is_rejected(
    test_settings: Settings, primed_cache: JwksCache, public_jwks
) -> None:
    """kid 不正: JWKS に存在しない kid を持つ token は BadSignatureError → 401 になる。

    joserfc は jwt.encode 時に header の kid を署名鍵の kid で自動設定する。
    JWKS に未登録の鍵で署名 → JWT の kid が JWKS にない → BadSignatureError が発生する。
    auth.py は attempt=0 で BadSignatureError → キャッシュクリアして retry する。
    retry 時の HTTP を避けるため load_jwks をモックし、同じ JWKS を返す。
    attempt=1 でも同じ kid が見つからないため、最終的に 401 になる。
    """
    other_key = RSAKey.generate_key(2048, {"kid": "attacker-key-999"}, private=True)
    payload   = make_valid_payload()
    token     = make_token(other_key, payload)

    with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
        verify = build_verify_access_token(test_settings, primed_cache)
        with pytest.raises(HTTPException) as exc_info:
            await verify(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["error_stage"] == "backend_authentication"
~~~

---

### exp 期限切れ（ExpiredTokenError）

**攻撃シナリオ**: ログアウト後や期限切れになった JWT を使い回して API にアクセスしようとする。

~~~python
async def test_expired_token(rsa_key, verify_token) -> None:
    """exp 期限切れ: 有効期限が過ぎた token は ExpiredTokenError → 401 になる。"""
    payload        = make_valid_payload()
    payload["exp"] = int(time.time()) - 600  # 10 分前に期限切れ
    token          = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
~~~

---

### exp 境界（leeway 内は通過）

サーバ間のクロックずれや処理遅延を考慮し、`clock_skew_seconds` の範囲内であれば「期限切れ直後」でも通す設定がある（leeway）。

~~~python
async def test_exp_boundary_within_leeway(rsa_key, primed_cache: JwksCache) -> None:
    """exp 境界: leeway=30s の設定では 10 秒前期限切れでも通る。

    clock_skew_seconds は JWTClaimsRegistry の leeway に渡される。
    NTP ずれや処理遅延を吸収するために設定する。
    """
    settings_with_leeway = Settings(
        keycloak_base_url="http://test-keycloak",
        keycloak_realm="test",
        jwks_cache_ttl_seconds=300,
        clock_skew_seconds=30,
        expected_audience=AUDIENCE,
    )
    verify = build_verify_access_token(settings_with_leeway, primed_cache)

    payload        = make_valid_payload()
    payload["exp"] = int(time.time()) - 10  # 10 秒前に期限切れ（leeway=30 秒以内）
    token          = make_token(rsa_key, payload)

    claims = await verify(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"
~~~

補足:

- `test_settings` fixture は `clock_skew_seconds=0` であるため、同じ payload を `verify_token` で検証すると `401` になる
- このテストでは `Settings` を直接インスタンス化して leeway あり・なしを比較している

---

### exp 欠落（設計上の把握ポイント）

~~~python
async def test_missing_exp(rsa_key, verify_token) -> None:
    """exp 欠落: exp がない token は validate() を通過する（設計上の把握ポイント）。

    RFC 7519 で exp は必須でなく、joserfc もデフォルトでは要求しない。
    必須化したい場合は JWTClaimsRegistry に exp={"essential": True} を追加する。
    """
    payload = make_valid_payload()
    del payload["exp"]
    token  = make_token(rsa_key, payload)

    claims = await verify_token(authorization=f"Bearer {token}")
    assert claims["sub"]      == "user-test-123"
    assert claims.get("exp") is None
~~~

補足:

- このテストは「例外が発生しないこと」を確認する。通過してしまうことを意図的に記録するテストである
- 本番で exp 欠落を拒否したい場合は `auth.py` の `JWTClaimsRegistry` に `exp={"essential": True}` を追加する

---

### aud 不一致（InvalidClaimError）

**攻撃シナリオ（confused deputy）**: 同じ Keycloak realm 内の別サービス（例: `other-service`）向けに発行された JWT を使って `demo-api` にアクセスしようとする。`aud` 検証でこの試みを弾く。

~~~python
async def test_wrong_audience(rsa_key, verify_token) -> None:
    """aud 不一致: 別サービス向けの token は InvalidClaimError（JoseError のサブクラス）→ 401 になる。

    confused deputy 攻撃（別サービス向けの token で API にアクセスする試み）の防御。
    """
    payload        = make_valid_payload()
    payload["aud"] = "other-service"
    token          = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
~~~

---

### iss 不一致（InvalidClaimError）

**攻撃シナリオ**: 攻撃者が別の Keycloak（または別の realm）を立て、そこで発行した JWT を正規の API に送りつける。`iss` 検証で想定外の発行元を弾く。

~~~python
async def test_wrong_issuer(rsa_key, verify_token) -> None:
    """iss 不一致: 別の realm から発行された token は InvalidClaimError（JoseError のサブクラス）→ 401 になる。

    iss 検証で、想定外の Keycloak realm やサードパーティが発行した token を弾く。
    """
    payload        = make_valid_payload()
    payload["iss"] = "http://evil-keycloak/realms/evil"
    token          = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
~~~

---

### 全テストを実行する

~~~zsh
cd apps/demo_api
pytest tests/ -v
~~~

期待する見え方:

~~~
asyncio: mode=Mode.AUTO
...
PASSED tests/test_auth.py::test_parse_bearer_token_missing_header
PASSED tests/test_auth.py::test_parse_bearer_token_invalid_scheme
PASSED tests/test_auth.py::test_parse_bearer_token_missing_token_value
PASSED tests/test_auth.py::test_parse_bearer_token_valid
PASSED tests/test_auth.py::test_extract_roles_empty_claims
PASSED tests/test_auth.py::test_extract_roles_no_realm_access
PASSED tests/test_auth.py::test_extract_roles_with_roles
PASSED tests/test_auth.py::test_extract_roles_non_list_is_ignored
PASSED tests/test_auth.py::test_build_claim_summary_structure
PASSED tests/test_auth.py::test_valid_token
PASSED tests/test_auth.py::test_tampered_payload
PASSED tests/test_auth.py::test_alg_none
PASSED tests/test_auth.py::test_token_signed_with_different_key_is_rejected
PASSED tests/test_auth.py::test_expired_token
PASSED tests/test_auth.py::test_exp_boundary_within_leeway
PASSED tests/test_auth.py::test_missing_exp
PASSED tests/test_auth.py::test_wrong_audience
PASSED tests/test_auth.py::test_wrong_issuer
~~~

判定:

- すべてのテストが `PASSED`
- ヘッダーに `asyncio: mode=Mode.AUTO` が表示される

------

## 失敗例

### 失敗例 1: `BadSignatureError` の retry で HTTP が呼ばれる

目的:

署名改ざんテストで `load_jwks` をモックしないと、retry 時に Keycloak への HTTP 接続が試みられ、テストが `503` で終わることを確認する。

再現方法:

1. `test_tampered_payload` から `patch("auth.load_jwks", ...)` の `with` ブロックを除去する
2. `verify = build_verify_access_token(test_settings, primed_cache)` を直接呼ぶ形に変更する
3. `pytest tests/test_auth.py::test_tampered_payload -v` を実行する

期待する見え方:

- `HTTPException(503, ...)` が発生してテストが失敗する
- `AssertionError: assert 503 == 401` のようなメッセージが表示される

補足:

- `BadSignatureError` が発生すると `auth.py` は `cache.clear()` して `force_refresh=True` で JWKS を再取得する
- テスト環境に Keycloak が存在しないため `httpx.RequestError` が発生し、`503` が返る
- `load_jwks` をモックすることで retry でも同じ JWKS が返り、2 回目の `BadSignatureError` で 401 になる

---

### 失敗例 2: `exp` 欠落で通過してしまう

目的:

`exp` を必須にしていないと、有効期限がない token が検証を通過することを確認する。

再現方法:

1. `test_missing_exp` の最後の assert が実行されることを確認する
2. `pytest tests/test_auth.py::test_missing_exp -v` を実行する

期待する見え方:

- テストが `PASSED`（例外が発生しない）
- `claims.get("exp") is None` が通る

補足:

- 必須化したい場合は `auth.py` の `JWTClaimsRegistry(...)` に `exp={"essential": True}` を追加する
- 追加すると `test_missing_exp` 側の期待値（`assert claims.get("exp") is None`）が `JoseError` → `HTTPException` に変わるため、テストも合わせて修正が必要になる

------

## 完了判定

- `apps/demo_api/tests/test_auth.py` に正常系・異常系のテストケースが実装されている
- `pytest tests/ -v` を実行してすべてのテストが green になる

------

## まとめ

この手順で理解したこと:

- JWT は 3 パーツ（ヘッダー・ペイロード・署名）から成り、署名検証でペイロードの改ざんを検出する
- Keycloak を起動せずにテストするために、テスト用 RSA 鍵ペアと JWKS モックを使う
- 署名改ざん（`BadSignatureError`）・`alg=none` 攻撃・`aud`/`iss` 不一致の 3 種の攻撃シナリオが、それぞれ 401 で弾かれることを確認した
- joserfc は kid が JWKS に存在しない場合も `BadSignatureError` として扱う。これにより例外処理を `JoseError` 系統に統一できている
- `auth.py` の retry ロジック（`BadSignatureError` → `cache.clear()` → `force_refresh` 再取得）は `patch("auth.load_jwks", ...)` でモックしてテストできる
- `exp` 欠落は joserfc のデフォルトでは検証されない。必要なら `JWTClaimsRegistry` で必須化する

ここまでで、「実装して終わり」ではなく「異常系も押さえた」状態になった。  
次は [11_SetupNextJsSPAWithPKCE.md](./11_SetupNextJsSPAWithPKCE.md) を参照し、Next.js SPA + PKCE 構成を確認する。

------

## 関連ドキュメント

- [docs/Reference/07_PytestAndMockBasics.md](./Reference/07_PytestAndMockBasics.md) — pytest・fixture・patch の基本概念
- [docs/Reference/05_TokenClaimsAndValidation.md](./Reference/05_TokenClaimsAndValidation.md) — claim の意味・検証順序・joserfc 例外型
- [docs/08_SetupAudienceValidation.md](./08_SetupAudienceValidation.md) — aud 検証の実装
