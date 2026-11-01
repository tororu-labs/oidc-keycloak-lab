# 01 Local Startup

## 目的

このドキュメントは、ローカルで Keycloak、BFF、Backend API を起動・停止し、基本的な動作確認を行うための共通手順を整理するものである。

------

## 前提

- `docs/03_SetupDocker-Keycloak.md` 以降の手順で必要なファイルが作成済みである
- `.venv` が作成済みである
- `apps/demo_bff/` と `apps/demo_api/` の依存関係が導入済みである

------

## 起動対象

- Keycloak
- BFF
- Backend API

------

## 使い分け

このラボでは、確認したい内容に応じて次の 2 パターンで起動することが多い。

- BFF 単体で確認する
  - `docs/05` の OIDC ログイン、session、`/me`、`/admin` を確認したいときに使う
- BFF と Backend API を同時に確認する
  - `docs/06` の `/api/me`、`/api/admin-data`、Bearer token 転送を確認したいときに使う

判断に迷った場合は、まず BFF 単体でログイン確認を行い、その後に Backend API を追加すると切り分けしやすい。

------

## 最低限の環境変数

### Keycloak と BFF の確認に必要なもの

- `KEYCLOAK_BASE_URL`
  - Keycloak のベース URL
  - 例: `http://localhost:8080`
- `KEYCLOAK_REALM`
  - 利用する realm 名
  - 例: `lab`
- `OIDC_CLIENT_ID`
  - BFF が使う Keycloak client ID
  - 例: `demo-bff`
- `OIDC_CLIENT_SECRET`
  - `demo-bff` client の secret
- `APP_BASE_URL`
  - BFF 自身のベース URL
  - 例: `http://localhost:8000`
- `SESSION_SECRET`
  - BFF の session cookie 署名に使う値
  - `OIDC_CLIENT_SECRET` とは別物である

### Backend API 連携時に追加するもの

- `BACKEND_API_BASE_URL`
  - BFF から呼び出す Backend API の URL
  - 例: `http://localhost:8001`

### Backend API 単体に必要なもの

- `KEYCLOAK_BASE_URL`
  - Keycloak の公開鍵取得元を決めるために使う
- `KEYCLOAK_REALM`
  - 検証対象の realm 名

------

## Keycloak の起動

~~~zsh
docker compose -f infra/keycloak/docker-compose.yml up -d
docker compose -f infra/keycloak/docker-compose.yml ps
~~~

- `http://localhost:8080` を開き、管理コンソールが表示されることを確認する
- 必要に応じて `docker compose -f infra/keycloak/docker-compose.yml logs` で状態を確認する

------

## パターン 1: BFF 単体で起動する

`docs/05` を進めるときの最小構成である。  
この時点では `BACKEND_API_BASE_URL` を設定しなくてもよい。

## BFF の起動

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export SESSION_SECRET="$(./.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

- `http://localhost:8000` を開き、トップページが表示されることを確認する
- `alice` は `/me` に到達でき、`/admin` は `403` になることを確認する
- `bob` は `/me` に到達でき、`/admin` に到達できることを確認する

------

## パターン 2: BFF と Backend API を同時に起動する

`docs/06` を進めるときの構成である。  
Backend API と BFF は別ターミナルで起動し、両方のログを見比べられる状態にしておく。

## Backend API の起動

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

- `http://localhost:8001/` を開き、保護対象ルートを示す JSON が表示されることを確認する

## BFF の起動

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export BACKEND_API_BASE_URL=http://localhost:8001
export SESSION_SECRET="$(./.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

- `http://localhost:8000/api/me` で `backend_status: 200` を確認する
- `alice` は `http://localhost:8000/api/admin-data` で `403` を確認する
- `bob` は `http://localhost:8000/api/admin-data` で `200` を確認する

------

## 動作確認

- Keycloak: `http://localhost:8080`
- BFF: `http://localhost:8000`
- Backend API: `http://localhost:8001`
- BFF ログイン確認:
  - `alice` は `/me` 成功かつ `/admin` が `403`
  - `bob` は `/me` 成功かつ `/admin` 成功
- BFF 経由 API 確認:
  - `alice` は `/api/admin-data` が `403`
  - `bob` は `/api/admin-data` が `200`

確認の目安:

- ログイン確認だけなら、まず BFF 単体で十分である
- `/api/*` の JSON を見る段階では、BFF と Backend API を両方起動する
- `502` が出たときは、認証失敗ではなく Backend API への接続失敗の可能性を先に疑う

------

## パターン 3: SPA + Backend API を起動する

`docs/11` を進めるときの構成である。  
Backend API と SPA は別ターミナルで起動する。BFF は不要。

### Backend API の起動（CORS 設定あり）

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export CORS_ALLOWED_ORIGINS=http://localhost:3000
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

### SPA の起動

~~~zsh
cd apps/demo_web_spa
npm install   # 初回のみ
npm run dev
~~~

- `http://localhost:3000` を開き、ログインボタンが表示されることを確認する
- Keycloak で `alice` ログイン後、「ログイン済み」と表示されることを確認する
- 「Backend API (/me) を直接呼ぶ」で `200` が返ることを確認する

------

## パターン 4: OTel あり（BFF + Backend API + OTel Collector + Jaeger）

`docs/13` を進めるときの構成である。  
パターン 2 の起動手順に OTel の環境変数を追加する。

### OTel インフラの起動

~~~zsh
docker compose -f infra/otel/docker-compose.yml up -d
~~~

- `http://localhost:16686` を開き、Jaeger UI が表示されることを確認する

### Backend API の起動（OTel あり）

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=demo-api
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

### BFF の起動（OTel あり）

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

補足:

- `OTEL_EXPORTER_OTLP_ENDPOINT` を省略すると OTel が無効（no-op）になり、パターン 2 と同じ挙動になる
- `OTEL_SERVICE_NAME` を省略すると BFF は `demo-bff`、API は `demo-api` がデフォルト値として使われる

------

## 停止方法

~~~zsh
# BFF / Backend API
Ctrl+C

# Keycloak
docker compose -f infra/keycloak/docker-compose.yml down

# OTel Collector + Jaeger
docker compose -f infra/otel/docker-compose.yml down
~~~

------

## 関連ドキュメント

- [03_SetupDocker-Keycloak.md](../03_SetupDocker-Keycloak.md)
- [05_SetupFastAPI-OIDCLogin.md](../05_SetupFastAPI-OIDCLogin.md)
- [06_SetupFastAPI-BackendAPI.md](../06_SetupFastAPI-BackendAPI.md)
