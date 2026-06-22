# 13 OpenTelemetry による認証フロー計装

## ここでのゴール

この手順では、BFF と Backend API に OpenTelemetry を導入し、次の状態に到達することをゴールとする。

- OTel Collector と Jaeger が Docker Compose で起動し、トレースを受信できる
- BFF と API のリクエストが、Jaeger UI で 1 本のトレースとして繋がって見える
- JWT 検証成功時に `auth.user.id`・`auth.result`、失敗時に `auth.failure.reason` がスパン属性として確認できる
- PII（email）がスパン属性に漏れた場合に、redaction processor でマスクできることを確認できる

必要な用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。  
OTel の概念的な背景は [09_Observability.md](./Reference/09_Observability.md) を参照する。

------

## 前提確認

- `docs/12` の手順が完了していること（BFF + Backend API + back-channel logout が動作する状態）
- Docker Desktop が起動していること
- `.venv` の依存関係に OTel パッケージが追加済みであること

判定:

- `pip show opentelemetry-sdk` でバージョン `1.42.1` が表示される
- `pip show opentelemetry-instrumentation-fastapi` でバージョン `0.63b1` が表示される

~~~zsh
pip show opentelemetry-sdk opentelemetry-instrumentation-fastapi
~~~

------

## この手順の流れ

この手順では、以下の流れで進める。

1. OTel Collector と Jaeger を起動する
2. BFF に OTel を導入する
3. BFF のトレースを Jaeger で確認する（自動計装だけで見えることを確認）
4. Backend API に OTel を導入する
5. context propagation を確認する（BFF → API が 1 本のトレースになることを確認）
6. カスタムスパン属性を確認する（`auth.user.id` / `auth.result` / `auth.failure.reason`）
7. 失敗例を再現する

------

## 1. OTel Collector と Jaeger を起動する

~~~zsh
docker compose -f infra/otel/docker-compose.yml up -d
docker compose -f infra/otel/docker-compose.yml ps
~~~

判定:

- `ps` の出力で `otel-collector` と `jaeger` がどちらも `running` になっている
- `http://localhost:16686` を開くと Jaeger UI が表示される

------

## 2. BFF に OTel を導入する

`apps/demo_bff/telemetry.py` と `apps/demo_bff/requirements.txt` はすでに更新済みである。  
パッケージを導入し、環境変数を付けて起動する。

~~~zsh
pip install -r apps/demo_bff/requirements.txt
~~~

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export BACKEND_API_BASE_URL=http://localhost:8001
export SESSION_SECRET="$(./.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=demo-bff
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

起動ログで次の行が出ることを確認する:

~~~
stage=otel_setup done service=demo-bff endpoint=http://localhost:4318
~~~

判定:

- `OTEL_EXPORTER_OTLP_ENDPOINT` を付けずに起動したとき、`stage=otel_setup skipped` とログが出てアプリが正常に起動する（no-op 確認）
- `OTEL_EXPORTER_OTLP_ENDPOINT` を付けて起動したとき、`stage=otel_setup done` が出る

------

## 3. BFF のトレースを Jaeger で確認する

BFF だけが OTel 済みの状態で `/login` → ログイン → `/me` の流れを実行し、Jaeger にトレースが届いているか確認する。

確認手順:

1. `http://localhost:8000/me` を開き、`alice` でログインする
2. `http://localhost:16686` を開く
3. 左の「Service」で `demo-bff` を選択し「Find Traces」をクリックする
4. `/auth/callback` や `/me` の HTTP リクエストがスパンとして表示されることを確認する

判定:

- Jaeger UI に `demo-bff` のトレースが表示される
- 各スパンに HTTP メソッド・パス・ステータスコードが含まれている

------

## 4. Backend API に OTel を導入する

~~~zsh
pip install -r apps/demo_api/requirements.txt
~~~

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=demo-api
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

判定:

- 起動ログに `stage=otel_setup done service=demo-api` が出る

------

## 5. context propagation を確認する

BFF と API の両方が起動した状態で `/api/me` を呼び出し、1 本のトレースとして繋がることを確認する。

確認手順:

1. `http://localhost:8000/api/me` を開く
2. Jaeger UI で `demo-bff` のトレースを探す
3. 対象のトレースをクリックして詳細を開く
4. スパン一覧に `demo-bff` と `demo-api` の両方が含まれていることを確認する

期待する見え方:

- 1 本のトレースの中に BFF のスパンと API のスパンが入れ子で表示される
- `demo-bff` が親スパン、`demo-api` が子スパンになっている
- 同一の `trace_id` を共有している

判定:

- BFF と API が同一 `trace_id` で繋がった 1 本のトレースとして Jaeger に表示される

------

## 6. カスタムスパン属性を確認する

`/api/me` を正常に呼び出した後、Jaeger でスパンの詳細を確認する。

確認手順:

1. Jaeger で `/me` のスパン（`demo-api` 側）を選択する
2. 「Tags」セクションに次の属性が含まれていることを確認する

期待する見え方:

| 属性名 | 値の例 |
|---|---|
| `auth.user.id` | `f7a3...`（Keycloak の sub claim、UUID 形式） |
| `auth.result` | `success` |

判定:

- `auth.user.id` と `auth.result` が Jaeger のスパン属性に表示される

------

## 7. 失敗例を再現する

### 失敗例 1: PII がスパン属性に漏れる

目的:

redaction なしでは email アドレスがそのままスパン属性に出ることを確認し、redaction processor の効果を体験する。

再現方法:

1. `apps/demo_api/auth.py` の `verify_access_token` 内の成功時スパン設定に次の行を一時追加する

~~~python
span.set_attribute("auth.user.email", result.claims.get("email", ""))
~~~

2. API を再起動し、`/api/me` を呼び出す
3. Jaeger UI でスパンの Tags を確認する

期待する見え方:

- `auth.user.email` の値が `****` などの形でマスクされている
  - redaction processor の `blocked_values` に email パターンが設定されているため
- Collector の stdout ログに `redaction processor: 1 value(s) redacted` のような行が出る

補足:

- 確認後は追加した行を削除する

------

### 失敗例 2: context propagation 漏れでトレースが分断される

目的:

`HTTPXClientInstrumentor` がない状態では BFF → API のトレースが繋がらないことを体験する。

再現方法:

1. `apps/demo_bff/telemetry.py` の `HTTPXClientInstrumentor().instrument()` の行をコメントアウトする
2. BFF を再起動し、`/api/me` を呼び出す
3. Jaeger で `demo-bff` と `demo-api` のトレースをそれぞれ確認する

期待する見え方:

- BFF と API がそれぞれ別の `trace_id` を持った独立したトレースとして表示される
- 1 本のトレースに BFF + API のスパンが入っていない

補足:

- 確認後はコメントアウトを元に戻す

------

### 失敗例 3: Collector が起動していなくてもアプリが落ちない

目的:

`OTEL_EXPORTER_OTLP_ENDPOINT` をセットした状態で Collector を停止しても、アプリが継続動作することを確認する。

再現方法:

1. `docker compose -f infra/otel/docker-compose.yml down` で Collector を停止する
2. `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` を付けたまま BFF を起動する
3. `http://localhost:8000/me` に通常どおりアクセスする

期待する見え方:

- アプリは正常に起動し、ログインやページ表示に影響はない
- uvicorn のログに `BatchSpanProcessor` の送信エラーが出ることがあるが、アプリは継続動作する

補足:

- `BatchSpanProcessor` は送信失敗を非同期でサイレントに処理するため、ユーザーへの影響はない

------

## 実行コマンド一覧

### OTel インフラ操作

~~~zsh
# 起動
docker compose -f infra/otel/docker-compose.yml up -d

# 状態確認
docker compose -f infra/otel/docker-compose.yml ps

# ログ確認（redaction の出力を見たいとき）
docker compose -f infra/otel/docker-compose.yml logs otel-collector

# 停止
docker compose -f infra/otel/docker-compose.yml down
~~~

------

## 完了判定

- OTel Collector と Jaeger が Docker Compose で起動する
- BFF と API のトレースが Jaeger UI で 1 本のトレースとして表示される
- `auth.user.id` と `auth.result` がスパン属性として確認できる
- `auth.user.email` を一時設定したとき、redaction で値がマスクされることを確認できる
- `OTEL_EXPORTER_OTLP_ENDPOINT` が未設定のとき、アプリが通常どおり起動する（no-op）

------

## まとめ

今回の手順で確認したこと:

- `OTEL_EXPORTER_OTLP_ENDPOINT` の有無で OTel の有効 / 無効を切り替えられる設計になっている
- FastAPIInstrumentor の自動計装で、コードを変えなくても HTTP リクエスト単位のスパンが取得できる
- `HTTPXClientInstrumentor` を追加するだけで BFF → API 間の `traceparent` ヘッダー伝搬が自動化される
- `auth.user.id`・`auth.result`・`auth.failure.reason` を付与することで、認証フローのどの段階で何が起きたかをトレースから追える
- redaction processor により、Collector 側で PII（email）を一元的にマスクできる

ここまでで、「動く認証基盤」に観測性を加えた状態になった。  
次は Phase 06（セキュリティ監査エージェント）または Phase 07（MCP サーバー）を進める。

------

## 関連ドキュメント

- [Reference/09_Observability.md](./Reference/09_Observability.md) — 分散トレーシングの概念と設計指針
- [Reference/01_LocalStartup.md](./Reference/01_LocalStartup.md) — 各パターンの起動手順（パターン 4: OTel あり）
- [Reference/00_Glossary.md](./Reference/00_Glossary.md) — 用語集
- [12_SetupRefreshAndLogout.md](./12_SetupRefreshAndLogout.md) — 前の手順（Refresh Token と Back-channel Logout）
