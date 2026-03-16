# Setup FastAPI Backend API

## 目的

このドキュメントは、FastAPI ベースの最小 OIDC ログイン検証を次の段階へ進め、BFF と Backend API を分離して Access Token による API 保護を確認するためのハンズオンを記録するものである。  
主な目的は以下の通り。

- `apps/demo_bff/` を BFF として使い、session から Access Token を取り出して別 API へ渡せるようにする
- `apps/demo_api/` を Backend API として追加し、Bearer token の署名、`iss`、`exp` を検証できるようにする
- `alice` と `bob` で `/api/me`、`/api/admin-data` の結果を比較し、BFF 側の session 管理と API 側の認可判定の違いを確認する
- 「ブラウザは Cookie を使い、API は JWT を検証する」という役割分担を体験する

### 用語

- Backend API: BFF の後段で動き、Bearer token を受け取って保護されたデータを返す API
- Bearer token: `Authorization: Bearer <token>` の形式で送る access token
- JWKS: JWT の署名検証に使う公開鍵セット
- issuer (`iss`): token を発行した主体

------

## 実施概要

今回のセットアップでは、以下の流れで作業を進める。

1. 新しい Backend API アプリ `apps/demo_api/` の依存関係をインストールする
2. BFF と Backend API の環境変数を設定する
3. Backend API を `http://localhost:8001` で起動する
4. BFF を `http://localhost:8000` で起動する
5. `alice` と `bob` でログインし、BFF 経由で `/api/me` と `/api/admin-data` を確認する

------

## 前提確認

この手順を始める前に、FastAPI 単体の OIDC ログイン確認が完了していることを前提とする。  
具体的には以下を満たしていることを確認する。

- `docs/05_SetupFastAPI-OIDCLogin.md` の手順が完了している
- `lab` realm に `alice`、`bob`、`viewer`、`admin`、`demo-bff` が存在する
- Keycloak が `http://localhost:8080` で起動している
- `demo-bff` client secret を使って BFF からログインできる

### 前提確認の判定

- `http://localhost:8000` で BFF のトップページが開く
- `alice` は `/me` に到達できる
- `bob` は `/admin` に到達できる

------

## アプリ構成

今回の段階では、アプリ構成は以下になる。

- `apps/demo_bff/main.py`
  - OIDC ログイン開始
  - callback で token 受信
  - session 管理
  - `/api/me`、`/api/admin-data` で Backend API を代理呼び出し
- `apps/demo_api/main.py`
  - `Authorization: Bearer <token>` を受け取る
  - Keycloak の公開鍵で JWT を検証する
  - role に応じてレスポンスを分ける

### アプリ構成の補足

- BFF はブラウザと session cookie ベースで通信する
- Backend API は Cookie を見ず、access token だけを見る
- 初回学習用として、Backend API では `aud` 検証はまだ行わない

------

## 依存関係のインストール

プロジェクトルートで仮想環境を有効化し、Backend API 用の依存関係を追加でインストールする。

~~~zsh
source .venv/bin/activate
python -m pip install -r apps/demo_api/requirements.txt
~~~

### 依存関係のインストールの補足

- `fastapi`: Backend API 本体
- `uvicorn`: 開発用サーバ
- `httpx`: Keycloak の JWKS を取得するために使う
- `authlib`: JWT の署名検証に使う

### 依存関係のインストールの判定

- `python -m pip install -r apps/demo_api/requirements.txt` が成功する
- `python -m pip show fastapi authlib uvicorn httpx` で導入を確認できる

------

## 環境変数の設定

Backend API 側では Keycloak の公開鍵取得先を知るために、Keycloak の URL と realm を設定する。  
BFF 側では既存の設定に加えて、呼び出し先 Backend API の URL を設定する。

~~~zsh
source .venv/bin/activate

# Backend API 用
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab

# BFF 用
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export BACKEND_API_BASE_URL=http://localhost:8001
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

### 環境変数の設定の補足

- `BACKEND_API_BASE_URL` は BFF が proxy 先を決めるために使う
- Backend API は `OIDC_CLIENT_SECRET` を使わない
- `SESSION_SECRET` は BFF 側だけで利用する

------

## Backend API の起動

まず Backend API を起動する。

~~~zsh
source .venv/bin/activate
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

別ターミナルで `http://localhost:8001/` を開くと、保護対象ルートや検証内容を示す JSON が表示される。

### Backend API 起動の判定

- `http://localhost:8001/` が開く
- `/me` と `/admin-data` が protected route として表示される

------

## BFF の起動

次に BFF を起動する。  
Backend API と BFF は別ターミナルで同時に起動し、どちらの `uvicorn` ログも確認できる状態にしておく。

~~~zsh
source .venv/bin/activate
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

### BFF 起動の補足

- `docs/05_SetupFastAPI-OIDCLogin.md` と同じ `demo-bff` client をそのまま使う
- `/api/me` と `/api/admin-data` は BFF の session を見てから Backend API を呼び出す
- 確認後は両方の `uvicorn` を `Ctrl+C` で停止する

------

## API アクセスフローの確認

ブラウザで `http://localhost:8000` を開き、Keycloak 経由でログインしたあとに BFF の `/api/*` を確認する。  
このとき、ブラウザは session cookie を送り、BFF は session から access token を取り出して Backend API へ Bearer token として転送する。

### `alice` で確認すること

1. `http://localhost:8000` を開く
2. `Keycloak でログイン` を押して `alice` でログインする
3. `http://localhost:8000/api/me` を開く
4. `backend_status` が `200` であることを確認する
5. `backend_response.user.preferred_username` が `alice` であることを確認する
6. `backend_response.user.roles` に `viewer` が含まれることを確認する
7. `http://localhost:8000/api/admin-data` を開く
8. `backend_status` が `403` であることを確認する

### `bob` で確認すること

1. logout する
2. 再度 `Keycloak でログイン` を押して `bob` でログインする
3. `http://localhost:8000/api/me` を開く
4. `backend_status` が `200` であることを確認する
5. `backend_response.user.preferred_username` が `bob` であることを確認する
6. `backend_response.user.roles` に `admin` が含まれることを確認する
7. `http://localhost:8000/api/admin-data` を開く
8. `backend_status` が `200` であることを確認する

### API アクセスフロー確認の補足

- `/api/me` は BFF 自体の `/me` とは異なり、Backend API が JWT を検証した結果を返す
- `/api/admin-data` は Backend API 側で `admin` role を要求する
- BFF は access token を転送するだけで、JWT の署名検証は Backend API 側で行う

### API アクセスフロー確認の判定

- `alice` は `/api/me` 成功かつ `/api/admin-data` が `403` になる
- `bob` は `/api/me` 成功かつ `/api/admin-data` 成功になる
- BFF のレスポンスに `backend_status` と `backend_response` が含まれる

------

## ログで見るポイント

この段階では、BFF と Backend API の両方のログを見ると役割の違いが分かりやすい。

- BFF の `uvicorn` ログ
  - `/login`
  - `/auth/callback`
  - `/api/me`
  - `/api/admin-data`
- Backend API の `uvicorn` ログ
  - `/me`
  - `/admin-data`
  - `alice` の `/admin-data` では `403`
  - `bob` の `/admin-data` では `200`

### ログ確認の補足

- BFF 側では session が有効であることを前提に proxy が行われる
- Backend API 側では Cookie を見ず、Bearer token だけで認可する
- ここが「session は BFF、JWT 検証は API」という役割分担の核心になる

------

## Backend API 停止時の確認

Backend API を停止した状態で `http://localhost:8000/api/me` または `http://localhost:8000/api/admin-data` を開くと、BFF 側で `502` を返すことがある。  
この場合は、BFF が session を持っていても downstream API へ到達できないため、代理呼び出しに失敗している。

### Backend API 停止時の確認の判定

- BFF 側のレスポンスで `detail` に接続失敗が表示される
- `backend_url` に `http://localhost:8001/...` が含まれる

------

## 本ドキュメントで完了したこと

- BFF と Backend API を FastAPI 同士で分離した
- BFF が session から access token を取り出して別 API に渡せるようになった
- Backend API が JWT の署名、`iss`、`exp` を検証する最小構成を確認できた
- `alice` と `bob` で API レベルの認可結果が分かれることを確認できた

## 完了判定

- `apps/demo_api/` の Backend API が起動する
- `apps/demo_bff/` の BFF から `/api/me` と `/api/admin-data` を呼べる
- `alice` は `/api/admin-data` で `403` になる
- `bob` は `/api/admin-data` に到達できる
- BFF と Backend API の役割分担を、自分の言葉で説明できる
