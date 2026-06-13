# Setup Audience Validation

## ここでのゴール

この手順では、`aud` 検証を Backend API に追加し、次の状態に到達することをゴールとする。

- Keycloak の `demo-bff` client に Audience Mapper を追加し、access token の `aud` に `demo-api` を付与できる
- Backend API の `config.py`、`auth.py`、`responses.py` を変更して `aud` 検証を有効にし、エンドポイントのレスポンスに反映できる
- `aud` が合わない token を送ったときに `401` が返ることを再現できる

必要な用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。

------

## 背景

`07_SetupTokenValidationAndFailureCases.md` まで、Backend API は token の署名・`iss`・`exp` を検証してきた。  
`http://localhost:8001/` のルートを開くと `"verification": ["signature", "iss", "exp"]` と表示されており、`aud` が未検証の状態であることを確認できる。

`aud`（Audience）は「この token を受け取るべきサービスはどれか」を示す claim である。  
`aud` を検証しないと、同じ realm で発行された別サービス向けの token でも Backend API を通過できてしまう。

この手順では、次の 2 つを組み合わせて `aud` 検証を完成させる。

- Keycloak 側: access token に `demo-api` を `aud` として付与する mapper を追加する
- Backend API 側: `EXPECTED_AUDIENCE` 環境変数を追加し、`claims_options` に `aud` 検証を追加する

------

## 前提確認

この手順を始める前に、以下が完了していることを確認する。

- `docs/07_SetupTokenValidationAndFailureCases.md` の手順が完了している
- Keycloak、BFF、Backend API の起動方法が分かっている
- `demo-bff` client が `http://localhost:8080` の `lab` realm に存在する

判定:

- `alice` でログインして `http://localhost:8000/api/me` が `200` を返す
- `http://localhost:8001/` の JSON に `"note": "この段階では audience 検証は行わない。"` が含まれる

------

## この手順の流れ

この手順では、以下の流れで進める。

1. `aud` claim の役割を整理する
2. Keycloak に Audience Mapper を追加する
3. Keycloak の評価画面で token の `aud` を確認する
4. Backend API の `config.py`、`auth.py`、`responses.py` を変更する
5. 正常系を確認する
6. 失敗例を再現する

------

## `aud` claim の役割

access token の `aud` claim は、その token を受け取るべきサービスの識別子（受信者）を表す。

~~~text
{
  "iss": "http://localhost:8080/realms/lab",
  "aud": ["account", "demo-api"],
  "azp": "demo-bff",
  ...
}
~~~

各 claim の意味を整理する。

| claim | 意味                           | 今回の値の例                               |
|-------|--------------------------------|--------------------------------------------|
| `iss` | token を発行した認証サーバー   | `http://localhost:8080/realms/lab`         |
| `aud` | token を受け取るべきサービス   | `["account", "demo-api"]`                  |
| `azp` | token を要求した client         | `demo-bff`                                 |

`aud` を検証することで、`demo-api` 宛でない token を `demo-api` が受け付けないことを保証できる。

補足:

- Keycloak は `account` client scope が付与されていると `account` を `aud` に含める
- `demo-api` を `aud` に追加するには、Audience Mapper が必要である

------

## Keycloak: Audience Mapper を追加する

`demo-bff` client の dedicated scope に Audience Mapper を追加し、access token の `aud` に `demo-api` を付与する。

実施手順:

1. `http://localhost:8080` の管理コンソールを開く
2. 左上で `lab` realm を選ぶ
3. 左メニューの `Clients` を開く
4. `demo-bff` を選ぶ
5. `Client scopes` タブを開く
6. `demo-bff-dedicated` のリンクをクリックする
7. `Add mapper` から `By configuration` を選ぶ
8. 一覧から `Audience` を選ぶ
9. 以下の値を入力して保存する

~~~text
Name:                      add-demo-api-audience
Included Custom Audience:  demo-api
Add to access token:       ON
Add to ID token:           OFF
~~~

判定:

- `demo-bff-dedicated` の mapper 一覧に `add-demo-api-audience` が表示される

補足:

- `Included Client Audience` は Keycloak に同名の client が存在する場合に使う項目である
- 今回は Backend API を Keycloak の client として登録しないため、`Included Custom Audience` に文字列で `demo-api` を入力する

------

## Keycloak の評価画面で `aud` を確認する

Audience Mapper を追加したあと、`demo-bff` client の token 評価画面で `aud` が変わったことを確認する。

確認手順:

1. 左メニューの `Clients > demo-bff` を開く
2. `Client scopes` タブを開く
3. `Evaluate` を選ぶ
4. `User` に `alice` を選ぶ
5. `Generated access token` を展開する

期待する見え方:

~~~text
"aud": [
  "account",
  "demo-api"
],
~~~

判定:

- `aud` に `demo-api` が含まれている
- `azp` は `demo-bff` のまま変わっていない

------

## Backend API のコード変更

`aud` 検証を有効にするために、`apps/demo_api/` 以下の 3 ファイルを変更する。

### `config.py` の変更

`expected_audience` フィールドを追加し、`EXPECTED_AUDIENCE` 環境変数から読み込む。

~~~python
@dataclass(frozen=True)
class Settings:
    keycloak_base_url: str
    keycloak_realm: str
    jwks_cache_ttl_seconds: int
    clock_skew_seconds: int
    expected_audience: str          # 追加
~~~

~~~python
def load_settings() -> Settings:
    return Settings(
        keycloak_base_url=os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/"),
        keycloak_realm=os.getenv("KEYCLOAK_REALM", "lab"),
        jwks_cache_ttl_seconds=int(os.getenv("JWKS_CACHE_TTL_SECONDS", "300")),
        clock_skew_seconds=int(os.getenv("CLOCK_SKEW_SECONDS", "30")),
        expected_audience=os.getenv("EXPECTED_AUDIENCE", "demo-api"),  # 追加
    )
~~~

### `auth.py` の変更

`build_verify_access_token` 内の `claims_options` に `aud` を追加する。

変更前:

~~~python
claims_options = {"iss": {"essential": True, "value": settings.issuer}}
~~~

変更後:

~~~python
claims_options = {
    "iss": {"essential": True, "value": settings.issuer},
    "aud": {"essential": True, "value": settings.expected_audience},
}
~~~

また、成功ログに `aud` を追加して確認しやすくする。

変更前:

~~~python
logger.info(
    "stage=backend_authentication_success user=%s iss=%s roles=%s",
    claims.get("preferred_username"),
    claims.get("iss"),
    extract_roles(dict(claims)),
)
~~~

変更後:

~~~python
logger.info(
    "stage=backend_authentication_success user=%s iss=%s aud=%s roles=%s",
    claims.get("preferred_username"),
    claims.get("iss"),
    claims.get("aud"),
    extract_roles(dict(claims)),
)
~~~

### `responses.py` の変更

`build_index_response` を変更して、`expected_audience` を表示し、`verification` から `aud` 未対応の note を取り除く。

変更前:

~~~python
def build_index_response(settings: Settings) -> dict[str, Any]:
    return {
        "name": "demo-api",
        "issuer": settings.issuer,
        "protected_routes": ["/me", "/admin-data"],
        "verification": ["signature", "iss", "exp"],
        "note": "この段階では audience 検証は行わない。",
    }
~~~

変更後:

~~~python
def build_index_response(settings: Settings) -> dict[str, Any]:
    return {
        "name": "demo-api",
        "issuer": settings.issuer,
        "expected_audience": settings.expected_audience,
        "protected_routes": ["/me", "/admin-data"],
        "verification": ["signature", "iss", "exp", "aud"],
    }
~~~

------

## 正常系の確認

コード変更後、Backend API を再起動して正常系を確認する。

~~~zsh
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

確認手順:

1. `alice` で `http://localhost:8000` にログインする
2. `http://localhost:8000/api/me` を開く
3. BFF 側と Backend API 側の `uvicorn` ログを確認する

期待する見え方:

- `http://localhost:8000/api/me` が `200` を返す
- `http://localhost:8001/` のルートに `"expected_audience": "demo-api"` と `"verification": ["signature", "iss", "exp", "aud"]` が含まれる
- Backend API の `uvicorn` ログに `stage=backend_authentication_success ... aud=['account', 'demo-api']` が表示される

判定:

- `alice` で `/api/me` が `200` を返す
- `bob` で `/api/admin-data` が `200` を返す
- ルートの `verification` に `aud` が含まれる

------

## 失敗例

### 失敗例 1: Audience Mapper なしで `aud` 検証を有効にする

目的:

Keycloak 側で `aud` が付与されていない token を使うと、`aud` 検証が通らないことを確認する。

再現方法:

1. Keycloak の `demo-bff-dedicated` から `add-demo-api-audience` mapper を削除する（または一時的に `Add to access token` を `OFF` にする）
2. 新しいセッションでログインし直す（Keycloak が発行済みの token は mapper 変更の影響を受けないため、ログアウト→再ログインして新しい token を取得する）
3. `http://localhost:8000/api/me` を開く

期待する見え方:

- `401 Unauthorized` が返る
- `error_stage` が `backend_authentication` になる
- Backend API の `uvicorn` ログに `stage=backend_authentication reason=jose_error detail=... aud` が表示される

補足:

- joserfc は `aud` が token に存在しない場合は `Missing claim: aud`、存在するが合わない場合は `Invalid claim: aud` を返す
- どちらのケースも `JoseError` を継承しているため、既存の `except JoseError` ブロックで捕捉される

------

### 失敗例 2: `EXPECTED_AUDIENCE` を意図的に変更する

目的:

Backend API が期待する `aud` と token の `aud` が一致しないと、正しい token でも `401` になることを確認する。

再現方法:

~~~zsh
export EXPECTED_AUDIENCE=wrong-service
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

その後 `http://localhost:8000/api/me` を開く。

期待する見え方:

- `401 Unauthorized` が返る
- `error_stage` が `backend_authentication` になる
- Backend API のログに `reason=jose_error detail=Invalid claim: aud` が表示される

確認後の戻し方:

~~~zsh
unset EXPECTED_AUDIENCE
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

補足:

- `EXPECTED_AUDIENCE` のデフォルト値は `demo-api` であるため、`unset` すれば元に戻る

------

## 実行コマンド一覧

### 起動コマンド

~~~zsh
# BFF
uvicorn main:app --app-dir apps/demo_bff --reload

# Backend API
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

### 失敗例再現用の環境変数

~~~zsh
# aud 不一致を再現する
export EXPECTED_AUDIENCE=wrong-service

# 元に戻す
unset EXPECTED_AUDIENCE
~~~

------

## 完了判定

- Keycloak の `demo-bff-dedicated` に `add-demo-api-audience` mapper が追加されている
- `demo-bff` の token 評価画面で `aud` に `demo-api` が表示される
- Backend API の `config.py` に `expected_audience` フィールドが追加されている
- `auth.py` の `claims_options` に `aud` 検証が追加されている
- `alice` で `/api/me` が `200` を返す
- `bob` で `/api/admin-data` が `200` を返す
- Audience Mapper を無効にすると `/api/me` が `401` になる
- `EXPECTED_AUDIENCE` を変更すると `/api/me` が `401` になる

------

## まとめ

今回の手順で確認したこと:

- `aud` claim は「この token を受け取るべきサービス」を識別するものであることを整理した
- Keycloak の Audience Mapper を使って access token に `demo-api` を `aud` として追加した
- Backend API に `EXPECTED_AUDIENCE` 環境変数と `aud` 検証を追加した
- mapper なしまたは `EXPECTED_AUDIENCE` 不一致で `401` になることを確認した

ここまでで、Backend API が `aud` を使って「自分宛ての token かどうか」を確認できる状態になった。  
次は client scope / mapper の設定を深め、Keycloak 側の設定が token の中身にどう影響するかを確認する。

------

## 関連ドキュメント

- [07_SetupTokenValidationAndFailureCases.md](./07_SetupTokenValidationAndFailureCases.md) を参照
- [06_SetupFastAPI-BackendAPI.md](./06_SetupFastAPI-BackendAPI.md) を参照
- [04_ClientAndTokenRoles.md](./Reference/04_ClientAndTokenRoles.md) を参照
- [03_Troubleshooting.md](./Reference/03_Troubleshooting.md) を参照
- [05_TokenClaimsAndValidation.md](./Reference/05_TokenClaimsAndValidation.md) — claim 検証の座学整理
