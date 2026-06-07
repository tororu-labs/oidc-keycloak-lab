# Setup JWT エッジケーステスト

## ここでのゴール

この手順では、`docs/08_SetupAudienceValidation.md` まで実装した JWT 検証ロジックを pytest で体系的に検証し、次の状態に到達することをゴールとする。

- JWKS をモック化してテスト用 RSA 鍵ペアを fixture 化できる
- 正常系に加え、署名改ざん・`alg=none` 攻撃・`aud` 不一致・`iss` 不一致・`exp` 境界など異常系を pytest で網羅できる
- 「ライブラリが暗黙で処理する部分」と「自分のコードが責任を持つ部分」の境界を言語化できる
- `pytest` 実行でテストがすべて green になる

用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。  
claim の意味・検証順序・例外型の詳細は [05_TokenClaimsAndValidation.md](./Reference/05_TokenClaimsAndValidation.md) を参照する。

------

## 前提確認

この手順を始める前に、以下が完了していることを確認する。

- `docs/08_SetupAudienceValidation.md` の手順が完了している
- `apps/demo_api/` の Python 仮想環境がセットアップされている

判定:

- `apps/demo_api/` で `pytest tests/` を実行したとき、既存のテストが通る

------

## この手順の流れ

この手順では、以下の流れで進める。

1. pytest の asyncio 設定を確認する
2. テスト用 RSA 鍵ペアと JWKS モックの仕組みを理解する
3. 各テストケースを実装・実行する

------

## pytest の asyncio 設定

`verify_access_token` は非同期関数であるため、`pytest-asyncio` が必要になる。

`pyproject.toml`（リポジトリルート）に以下の設定を追加する。

~~~toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
~~~

この設定を入れることで、`async def test_xxx()` と書いた関数を `@pytest.mark.asyncio` なしで実行できる。

判定:

- `pytest tests/` を実行したとき、`asyncio: mode=Mode.AUTO` がヘッダーに表示される

------

## JWKS モックの仕組み

実際の Keycloak に接続しない状態でも JWT 検証をテストするために、テスト用 RSA 鍵ペアを生成して `JwksCache` に直接格納する。

### テスト鍵の生成と公開鍵 JWKS の準備

~~~python
from joserfc import jwt
from joserfc.jwk import KeySet, RSAKey

# joserfc では generate_key の第 2 引数にパラメータ dict を渡すことで kid を直接付与できる。
rsa_key = RSAKey.generate_key(2048, {"kid": "test-kid-1"}, private=True)

# 公開鍵のみの JWKS（Keycloak JWKS エンドポイントと同じ構成）
pub_dict = rsa_key.as_dict(private=False)
public_jwks = KeySet.import_key_set({"keys": [pub_dict]})
~~~

補足:

- `as_dict(private=False)` は公開鍵コンポーネント（`n`, `e`）のみを返す
- joserfc は `jwt.encode` 時に JWT header の kid を署名鍵の kid で自動設定するため、鍵に kid を付与しておく必要がある
- joserfc では kid が JWKS に存在しない場合も `BadSignatureError`（`JoseError` サブクラス）が発生するため、authlib 時代に必要だった `except ValueError` ブロックは不要

### キャッシュへの事前格納

~~~python
from jwks_cache import JwksCache

cache = JwksCache(ttl_seconds=3600)
cache.set(public_jwks)
~~~

キャッシュに公開鍵が入っているため、`verify_access_token` が最初に `load_jwks` を呼んだとき HTTP を使わずキャッシュから返す。

判定:

- `public_jwks` を格納した cache を使う fixture が用意できている
- `jwt.encode(header, payload, rsa_key)` でテスト JWT を作れる

------

## テスト用 JWT 生成ヘルパー

テスト全体で使う共通ヘルパーを定義する。各テストでは `make_valid_payload()` の戻り値を必要な部分だけ上書きして使う。

~~~python
import base64, json, time

ISSUER   = "http://test-keycloak/realms/test"
AUDIENCE = "demo-api"

def make_valid_payload() -> dict:
    now = int(time.time())
    return {
        "iss": ISSUER, "sub": "user-test-123", "aud": AUDIENCE,
        "azp": "demo-bff", "exp": now + 300, "iat": now,
        "realm_access": {"roles": ["viewer"]},
    }

def make_token(rsa_key, payload, *, alg="RS256") -> str:
    # joserfc の jwt.encode は str を返す。kid は rsa_key.kid が header に自動設定される。
    return jwt.encode({"alg": alg}, payload, rsa_key)

def make_none_alg_token(payload: dict) -> str:
    """alg=none の JWT を手動で組み立てる（joserfc の encode を通さない）。"""
    header = {"alg": "none", "typ": "JWT"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{h}.{p}."

def tamper_payload(token: str, overrides: dict) -> str:
    """payload を書き換えて署名はそのままにする（署名不一致を意図的に作る）。"""
    parts = token.split(".")
    pad   = "=" * (4 - len(parts[1]) % 4)
    data  = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
    data.update(overrides)
    new_p = base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    return f"{parts[0]}.{new_p}.{parts[2]}"
~~~

------

## テストケースの実装と実行

### 正常系

```python
async def test_valid_token(rsa_key, verify_token):
    payload = make_valid_payload()
    token   = make_token(rsa_key, payload)
    claims  = await verify_token(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"
```

判定:

- `claims["iss"]` が `ISSUER`、`claims["aud"]` が `AUDIENCE` に一致する

---

### 署名改ざん（BadSignatureError）

```python
async def test_tampered_payload(rsa_key, test_settings, primed_cache, public_jwks):
    payload  = make_valid_payload()
    token    = make_token(rsa_key, payload)
    tampered = tamper_payload(token, {"sub": "attacker-injected"})

    # BadSignatureError → auth.py はキャッシュクリアして retry する
    # retry 時の HTTP を避けるため load_jwks をモックする
    with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
        verify = build_verify_access_token(test_settings, primed_cache)
        with pytest.raises(HTTPException) as exc_info:
            await verify(authorization=f"Bearer {tampered}")
    assert exc_info.value.status_code == 401
```

補足:

- `BadSignatureError` が発生すると `auth.py` はキャッシュをクリアして `force_refresh=True` で再取得を試みる
- テストでは retry の HTTP 呼び出しを `unittest.mock.patch` で差し替えている

判定:

- HTTPException が status_code=401 で発生する

---

### alg=none 攻撃（JoseError）

```python
async def test_alg_none(verify_token):
    payload    = make_valid_payload()
    none_token = make_none_alg_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {none_token}")
    assert exc_info.value.status_code == 401
```

補足:

- authlib は `none` アルゴリズムを登録していないため、JWKS へのキー検索が失敗して `JoseError` を送出する
- `auth.py` の `except JoseError` で捕捉されて 401 になる

---

### 未知の kid（ValueError → 401）

```python
async def test_token_signed_with_different_key_is_rejected(test_settings, primed_cache, public_jwks):
    # joserfc では kid 不一致も BadSignatureError（JoseError）として扱われる。
    # retry 時の HTTP を避けるため load_jwks をモックする。
    other_key = RSAKey.generate_key(2048, {"kid": "attacker-key-999"}, private=True)

    payload = make_valid_payload()
    token   = make_token(other_key, payload)  # kid = "attacker-key-999" が header に入る

    with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
        verify = build_verify_access_token(test_settings, primed_cache)
        with pytest.raises(HTTPException) as exc_info:
            await verify(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
```

判定:

- 401 が返ることをテストで確認できる

---

### exp 期限切れ（ExpiredTokenError）

```python
async def test_expired_token(rsa_key, verify_token):
    payload       = make_valid_payload()
    payload["exp"] = int(time.time()) - 600   # 10 分前
    token         = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
```

---

### exp 境界（leeway 内は通過）

```python
async def test_exp_boundary_within_leeway(rsa_key, primed_cache):
    settings = Settings(..., clock_skew_seconds=30, ...)
    verify   = build_verify_access_token(settings, primed_cache)

    payload        = make_valid_payload()
    payload["exp"] = int(time.time()) - 10  # 10 秒前に期限切れ（leeway=30 秒以内）
    token          = make_token(rsa_key, payload)

    claims = await verify(authorization=f"Bearer {token}")
    assert claims["sub"] == "user-test-123"
```

補足:

- `clock_skew_seconds` は `claims.validate(leeway=...)` に渡される
- NTP ずれや処理遅延を吸収するために設定する。本番では 30〜60 秒程度が一般的

---

### exp 欠落（設計上の把握ポイント）

```python
async def test_missing_exp(rsa_key, verify_token):
    payload = make_valid_payload()
    del payload["exp"]                      # exp を意図的に除去
    token  = make_token(rsa_key, payload)

    claims = await verify_token(authorization=f"Bearer {token}")
    assert claims.get("exp") is None        # 検証を通過してしまう
```

補足:

- RFC 7519 で `exp` は必須でなく、authlib もデフォルトでは要求しない
- 永続する token（exp なし）を受け入れたくない場合は `claims_options` に `"exp": {"essential": True}` を追加する

---

### aud 不一致（InvalidClaimError）

```python
async def test_wrong_audience(rsa_key, verify_token):
    payload        = make_valid_payload()
    payload["aud"] = "other-service"
    token          = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
```

補足:

- confused deputy 攻撃（別サービス向けの token で API にアクセスする試み）の防御
- `claims_options` の `"aud": {"essential": True, "value": settings.expected_audience}` が機能している

---

### iss 不一致（InvalidClaimError）

```python
async def test_wrong_issuer(rsa_key, verify_token):
    payload        = make_valid_payload()
    payload["iss"] = "http://evil-keycloak/realms/evil"
    token          = make_token(rsa_key, payload)
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
```

---

### テストの実行

~~~zsh
# apps/demo_api/ ディレクトリで実行する
cd apps/demo_api
pytest tests/ -v
~~~

期待する見え方:

- すべてのテストが `PASSED`
- ヘッダーに `asyncio: mode=Mode.AUTO` が表示される

------

## 失敗例

### `BadSignatureError` の retry で HTTP が呼ばれる

目的:

署名改ざんテストで `load_jwks` をモックしないと、retry 時に Keycloak への HTTP 接続が試みられ、テストが 503 で終わる。

再現方法:

1. `test_tampered_payload` から `patch("auth.load_jwks", ...)` を除去する
2. `pytest tests/test_auth.py::test_tampered_payload` を実行する

期待する見え方:

- `HTTPException(503, ...)` が発生してテストが失敗する

補足:

- `BadSignatureError` が発生すると `auth.py` はキャッシュをクリアして `force_refresh=True` で再取得を試みる。テスト環境に Keycloak がないため 503 になる
- `load_jwks` をモックすることで retry でも同じ JWKS が返り、2 回目の `BadSignatureError` で 401 になる

---

### `exp` 欠落で通過してしまう

目的:

`exp` を必須にしていないと、有効期限がない token が通過することを確認する。

再現方法:

1. `test_missing_exp` の `assert claims.get("exp") is None` の行が実行されることを確認する

期待する見え方:

- テストが `PASSED`（例外が発生しない）
- 必須化したい場合は `claims_options` に `"exp": {"essential": True}` を追加することで `MissingClaimError` が発生するようになる

------

## 完了判定

- `docs/10_SetupJWTEdgeCaseTests.md` が作成されている
- `apps/demo_api/tests/test_auth.py` に正常系・異常系のテストケースが実装されている
- `pytest tests/` を実行してすべてのテストが green になる

------

## まとめ

今回の手順で確認したこと:

- テスト用 RSA 鍵ペアと JWKS モックで、Keycloak なしに JWT 検証をテストできる
- 署名改ざん（`BadSignatureError`）・`alg=none` 攻撃（`JoseError`）・`aud`/`iss` 不一致（`InvalidClaimError`）など、各異常系が適切に 401 になることを確認できた
- `exp` 欠落は authlib のデフォルトでは検証されないため、必要なら `essential: True` で必須化する
- joserfc は jwt.encode 時に `kid` を署名鍵の kid で自動設定する。未知の kid も `BadSignatureError`（`JoseError` サブクラス）として扱われるため、例外処理が `JoseError` 系統に統一できた

ここまでで、「実装して終わり」ではなく「異常系も押さえた」状態になった。  
次は Phase 03: Next.js SPA + PKCE 構成を進める。

------

## 関連ドキュメント

- [docs/Reference/05_TokenClaimsAndValidation.md](./Reference/05_TokenClaimsAndValidation.md) — claim の意味・検証順序・Authlib 例外型
- [docs/08_SetupAudienceValidation.md](./08_SetupAudienceValidation.md) — aud 検証の実装
