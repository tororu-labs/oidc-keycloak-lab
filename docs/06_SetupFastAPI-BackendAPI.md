# Setup FastAPI Backend API

## ここでのゴール

この手順では、BFF と Backend API を分離し、Access Token を使った API 保護を確認する。  
次の状態に到達することをゴールとする。

- `apps/demo_bff/` を BFF として使い、session から Access Token を取り出して別 API へ渡せるようにする
- `apps/demo_api/` を Backend API として追加し、Bearer token の署名、`iss`、`exp` を検証できるようにする
- `alice` と `bob` で `/api/me`、`/api/admin-data` の結果を比較し、BFF 側の session 管理と API 側の認可判定の違いを確認する
- 「ブラウザは Cookie を使い、API は JWT を検証する」という役割分担を体験する

必要な用語は [00_Glossary.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/00_Glossary.md) を参照する。  
全体の役割分担は [02_AuthFlowArchitecture.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/02_AuthFlowArchitecture.md) に整理した。

------

## 前提確認

この手順を始める前に、FastAPI 単体の OIDC ログイン確認が完了していることを前提とする。  
具体的には以下を満たしていることを確認する。

- `docs/05_SetupFastAPI-OIDCLogin.md` の手順が完了している
- `lab` realm に `alice`、`bob`、`viewer`、`admin`、`demo-bff` が存在する
- Keycloak が `http://localhost:8080` で起動している
- `demo-bff` client secret を使って BFF からログインできる

判定:

- `http://localhost:8000` で BFF のトップページが開く
- `alice` は `/me` に到達できる
- `bob` は `/admin` に到達できる

------

## この手順の流れ

この手順では、以下の流れで進める。

1. 新しい Backend API アプリ `apps/demo_api/` の依存関係をインストールする
2. BFF と Backend API の環境変数を設定する
3. Backend API を `http://localhost:8001` で起動する
4. BFF を `http://localhost:8000` で起動する
5. `alice` と `bob` でログインし、BFF 経由で `/api/me` と `/api/admin-data` を確認する
6. Backend API 停止時の挙動を確認する

------

## この手順で使う画面とエンドポイント

今回の手順では、BFF と Backend API の両方を使い、次の URL やエンドポイントを確認する。

- `http://localhost:8000`
- `http://localhost:8000/api/me`
- `http://localhost:8000/api/admin-data`
- `http://localhost:8001/`
- `http://localhost:8001/me`
- `http://localhost:8001/admin-data`

補足:

- BFF と Backend API の役割差は [02_AuthFlowArchitecture.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/02_AuthFlowArchitecture.md) を参照する

------

## 依存関係のインストール

プロジェクトルートで仮想環境を有効化し、Backend API 用の依存関係を追加でインストールする。  
新しいターミナルを開いた直後や、VSCode 上でインストール行だけを単独実行した場合は `python` がシステム環境を向くことがある。導入コマンドは `.venv` の Python を明示して実行する。

~~~zsh
source .venv/bin/activate
./.venv/bin/python -m pip install -r apps/demo_api/requirements.txt
~~~

判定:

- `./.venv/bin/python -m pip install -r apps/demo_api/requirements.txt` が成功する
- `./.venv/bin/python -m pip show fastapi authlib uvicorn httpx` で導入を確認できる

------

## 環境変数の設定

Backend API 側では Keycloak の公開鍵取得先を知るために、Keycloak の URL と realm を設定する。  
BFF 側では既存の設定に加えて、呼び出し先 Backend API の URL を設定する。

`export` した環境変数は、そのコマンドを実行したシェルにしか残らない。  
この手順では Backend API と BFF を別ターミナルで起動するため、必要な値をそれぞれのターミナルで設定する。  
起動パターンの整理や、各変数をどこで使うかは [01_LocalStartup.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/01_LocalStartup.md) を参照する。

~~~zsh
# ターミナルA: Backend API 用
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
~~~

~~~zsh
# ターミナルB: BFF 用
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export BACKEND_API_BASE_URL=http://localhost:8001
export SESSION_SECRET="$(./.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

補足:

- `BACKEND_API_BASE_URL` は BFF が proxy 先を決めるために使う
- Backend API は `OIDC_CLIENT_SECRET` を使わない
- `SESSION_SECRET` は BFF 側だけで利用する

------

## Backend API の起動

まず Backend API を起動する。

~~~zsh
# 上の「ターミナルA」で実行する
source .venv/bin/activate
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

別ターミナルで `http://localhost:8001/` を開くと、保護対象ルートや検証内容を示す JSON が表示される。

判定:

- `http://localhost:8001/` が開く
- `/me` と `/admin-data` が protected route として表示される

------

## BFF の起動

次に BFF を起動する。  
Backend API と BFF は別ターミナルで同時に起動し、どちらの `uvicorn` ログも確認できる状態にしておく。

~~~zsh
# 上の「ターミナルB」で実行する
source .venv/bin/activate
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

判定:

- `http://localhost:8000` が開く
- BFF が `demo-bff` client を使ってログイン開始できる

補足:

- BFF 用ターミナルでは `OIDC_CLIENT_SECRET` と `SESSION_SECRET` が設定済みであることを確認する
- 確認後は両方の `uvicorn` を `Ctrl+C` で停止する

------

## API アクセスフローの確認

ブラウザで `http://localhost:8000` を開き、Keycloak 経由でログインしたあとに BFF の `/api/*` を確認する。  
このとき、ブラウザは session cookie を送り、BFF は session から access token を取り出して Backend API へ Bearer token として転送する。

この段階では、`backend_status` に加えて `error_stage` も確認する。  
正常系では `error_stage` は `null` になり、失敗時は原因に応じた値が入る。

### `alice` で確認すること

1. `http://localhost:8000` を開く
2. `Keycloak でログイン` を押して `alice` でログインする
3. `http://localhost:8000/api/me` を開く
4. `backend_status` が `200` であることを確認する
5. `error_stage` が `null` であることを確認する
6. `backend_response.user.preferred_username` が `alice` であることを確認する
7. `backend_response.user.roles` に `viewer` が含まれることを確認する
8. `http://localhost:8000/api/admin-data` を開く
9. `backend_status` が `403` であることを確認する
10. `error_stage` が `backend_authorization` であることを確認する

### `bob` で確認すること

1. `http://localhost:8000/` に戻る
2. ログイン済みトップページの `ログアウト` を押す
3. 再度 `Keycloak でログイン` を押して `bob` でログインする
4. `http://localhost:8000/api/me` を開く
5. `backend_status` が `200` であることを確認する
6. `error_stage` が `null` であることを確認する
7. `backend_response.user.preferred_username` が `bob` であることを確認する
8. `backend_response.user.roles` に `admin` が含まれることを確認する
9. `http://localhost:8000/api/admin-data` を開く
10. `backend_status` が `200` であることを確認する
11. `error_stage` が `null` であることを確認する

判定:

- `alice` は `/api/me` 成功かつ `/api/admin-data` が `403` になる
- `bob` は `/api/me` 成功かつ `/api/admin-data` 成功になる
- BFF のレスポンスに `backend_status`、`error_stage`、`backend_response` が含まれる

補足:

- `/api/me` は BFF 自体の `/me` とは異なり、Backend API が JWT を検証した結果を返す
- `/api/admin-data` は Backend API 側で `admin` role を要求する
- BFF は access token を転送するだけで、JWT の署名検証は Backend API 側で行う
- 失敗時の `error_stage` の意味一覧は [03_Troubleshooting.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/03_Troubleshooting.md) を参照する
- `/api/*` の確認後にユーザーを切り替えるときは、いったんトップページへ戻って `ログアウト` を押す

------

## 実行コマンド一覧

### Backend API 依存関係

~~~zsh
source .venv/bin/activate
./.venv/bin/python -m pip install -r apps/demo_api/requirements.txt
~~~

### 起動コマンド

~~~zsh
# Backend API
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload

# BFF
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

共通の起動・停止・確認観点は [01_LocalStartup.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/01_LocalStartup.md) を参照する。

------

## 完了判定

- `apps/demo_api/` の Backend API が起動する
- `apps/demo_bff/` の BFF から `/api/me` と `/api/admin-data` を呼べる
- `alice` は `/api/admin-data` で `403` になる
- `bob` は `/api/admin-data` に到達できる
- BFF と Backend API の役割分担を、自分の言葉で説明できる

------

## まとめ

今回の手順で確認したこと:

- BFF と Backend API を FastAPI 同士で分離した
- BFF が session から access token を取り出して別 API に渡せることを確認した
- Backend API が Access Token を検証して API 保護を行う最小構成を確認した
- `alice` と `bob` で API レベルの認可結果が分かれることを確認した

ここまでで、BFF と Backend API を分離した最小構成で API 保護を確認できた。  
次は [07_SetupTokenValidationAndFailureCases.md](./07_SetupTokenValidationAndFailureCases.md) を参照し、token 検証観点と代表的な失敗例を確認する。

------

## 関連ドキュメント

- [05_SetupFastAPI-OIDCLogin.md](./05_SetupFastAPI-OIDCLogin.md) を参照
- [07_SetupTokenValidationAndFailureCases.md](./07_SetupTokenValidationAndFailureCases.md) を参照
- [01_LocalStartup.md](./Reference/01_LocalStartup.md) を参照
- [02_AuthFlowArchitecture.md](./Reference/02_AuthFlowArchitecture.md) を参照
- [03_Troubleshooting.md](./Reference/03_Troubleshooting.md) を参照
- [04_ClientAndTokenRoles.md](./Reference/04_ClientAndTokenRoles.md) を参照
- [main.py](../apps/demo_bff/main.py) を参照
- [main.py](../apps/demo_api/main.py) を参照
