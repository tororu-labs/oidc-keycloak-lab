# Setup FastAPI OIDC Login

## ここでのゴール

この手順では、FastAPI を使って Keycloak の OIDC ログインを最小構成で確認し、次の状態に到達することをゴールとする。

- Keycloak に `demo-bff` client を追加し、FastAPI から認可コードフローを開始できるようにする
- FastAPI が `/login` と `/auth/callback` を通じて token を受け取れるようにする
- session を使ってログイン状態を保持し、`/me` と `/admin` で認証・認可結果を確認できるようにする
- `alice` と `bob` の role 差分がアプリ側の挙動にどう反映されるかを確認する

必要な用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。  
この段階で扱う BFF、session、token の役割分担は [02_AuthFlowArchitecture.md](./Reference/02_AuthFlowArchitecture.md) に整理した。

------

## 前提確認

この手順を始める前に、Keycloak の GUI セットアップが完了していることを確認する。  
具体的には、以下を満たしていることを前提とする。

- `lab` realm が存在する
- `alice` と `bob` の user が存在する
- `viewer` と `admin` の realm role が存在する
- Keycloak が `http://localhost:8080` で起動している

判定:

- `http://localhost:8080` の管理コンソールへ入れる
- `lab` realm の `Users` と `Realm roles` を確認できる

------

## この手順の流れ

この手順では、以下の流れで進める。

1. Keycloak で `demo-bff` client を作成する
2. FastAPI アプリの依存関係をインストールする
3. 環境変数を設定してアプリを起動する
4. `/login` から Keycloak へログインし、`/me` と `/admin` を確認する
5. `alice` と `bob` の role 差分、および logout 後の状態を確認する

------

## `demo-bff` Client の作成

FastAPI から認可コードフローを開始するため、Keycloak 側に confidential client を追加する。

実施手順:

1. `lab` realm を開く
2. `Clients` を開く
3. `Create client` を押す
4. `Client type` は `OpenID Connect` を選ぶ
5. `Client ID` に `demo-bff` を入力する
6. `Next` を押す
7. `Client authentication` を `ON` にする
8. `Authorization` は `OFF` のままにする
9. `Standard flow` が `ON` であることを確認する
10. 保存する

保存後、`Settings` タブで以下を設定する。

~~~text
Root URL: http://localhost:8000
Home URL: http://localhost:8000/
Valid redirect URIs: http://localhost:8000/auth/callback
Valid post logout redirect URIs: http://localhost:8000/
Web origins: http://localhost:8000
~~~

続いて `Credentials` タブを開き、表示された secret を控える。  
この secret は後で `OIDC_CLIENT_SECRET` に設定する。

判定:

- `Clients` 一覧に `demo-bff` が存在する
- `Client authentication` が `ON` である
- `Valid redirect URIs` に `http://localhost:8000/auth/callback` が設定されている
- `Credentials` タブで secret を確認できる

補足:

- ここでは FastAPI 側で token を扱うため、confidential client を使う
- `redirect URI` と `post logout redirect URI` は Keycloak 側の戻り先制御に使う

------

## この手順で使う画面とエンドポイント

今回追加したアプリは `apps/demo_bff/` に置いてある。  
この手順では、`/login`、`/auth/callback`、`/me`、`/admin`、`/logout` を使って OIDC ログインと role 差分を確認する。BFF の役割分担は、必要に応じて [02_AuthFlowArchitecture.md](./Reference/02_AuthFlowArchitecture.md) を参照する。

------

## 依存関係のインストール

プロジェクトルートで仮想環境を有効化し、依存関係をインストールする。  
新しいターミナルを開いた直後や、VSCode 上でインストール行だけを単独実行した場合は `python` がシステム環境を向くことがあるため、導入コマンドは `.venv` の Python を明示して実行する。

~~~zsh
source .venv/bin/activate
./.venv/bin/python -m pip install -r apps/demo_bff/requirements.txt
~~~

判定:

- `./.venv/bin/python -m pip install -r apps/demo_bff/requirements.txt` が成功する
- `./.venv/bin/python -m pip show fastapi authlib uvicorn httpx itsdangerous` で導入を確認できる

------

## 環境変数の設定

`.env.example` を参考に、実行用の環境変数を設定する。  
ここでは BFF 単体確認に必要な最小構成だけを記載する。  
起動時に使う環境変数の意味や、BFF 単体と BFF + Backend API の使い分けは [01_LocalStartup.md](./Reference/01_LocalStartup.md) を参照する。

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

補足:

- `OIDC_CLIENT_SECRET` は Keycloak の `Credentials` タブで確認した値を使う
- `SESSION_SECRET` は Cookie 署名用であり、`OIDC_CLIENT_SECRET` とは別物である

------

## FastAPI アプリの起動

環境変数を設定した状態で、開発サーバを起動する。

~~~zsh
source .venv/bin/activate
uvicorn main:app --app-dir apps/demo_bff --reload
~~~

ブラウザで `http://localhost:8000` を開くと、未ログイン状態のトップページが表示される。

判定:

- `http://localhost:8000` が開く
- 未ログイン時のトップページに `Keycloak でログイン` ボタンが表示される
- `OIDC_CLIENT_SECRET` と `SESSION_SECRET` が未設定の場合は、設定不足を示すメッセージが表示される

------

## ログインフローの確認

`/login` から Keycloak に遷移し、`alice` または `bob` でログインする。  
ログイン成功後、FastAPI は `/auth/callback` で token を受け取り、session を作成して `/me` へリダイレクトする。

### `alice` で確認すること

1. `http://localhost:8000` を開く
2. `Keycloak でログイン` を押す
3. Keycloak のログイン画面で `alice` の資格情報を入力する
4. `/me` へ戻ったあと、`preferred_username` が `alice` であることを確認する
5. role 一覧に `viewer` が含まれることを確認する
6. `/admin` を開き、`403 Forbidden` になることを確認する

### `bob` で確認すること

1. `http://localhost:8000/` に戻る
2. ログイン済み画面の `ログアウト` を押す
3. 再度 `Keycloak でログイン` を押す
4. `bob` の資格情報でログインする
5. `/me` で `preferred_username` が `bob` であることを確認する
6. role 一覧に `admin` が含まれることを確認する
7. `/admin` を開き、アクセス成功となることを確認する

判定:

- `alice` は `/me` へ到達できる
- `alice` は `/admin` で `403` になる
- `bob` は `/me` へ到達できる
- `bob` は `/admin` へ到達できる

補足:

- `/me` は「誰としてログインしたか」を見る場所である
- `/admin` は「何ができるか」を見る場所である

------

## Logout の確認

トップページまたはログイン済み画面から `ログアウト` を実行する。  
FastAPI はローカル session を削除し、その後 Keycloak の logout endpoint へ遷移する。

判定:

- logout 後にトップページへ戻る
- `/me` または `/admin` を開くと再ログインが必要になる

補足:

- OIDC ログインまわりの失敗例は [07_SetupTokenValidationAndFailureCases.md](./07_SetupTokenValidationAndFailureCases.md) を参照する
- 切り分け観点は [03_Troubleshooting.md](./Reference/03_Troubleshooting.md) に整理した

------

## 実行コマンド一覧

### 依存関係と起動

~~~zsh
source .venv/bin/activate # 仮想環境を有効化
./.venv/bin/python -m pip install -r apps/demo_bff/requirements.txt # 依存関係を導入
uvicorn main:app --app-dir apps/demo_bff --reload # FastAPI アプリを起動
~~~

### 環境変数設定例

~~~zsh
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

共通の起動・停止・確認観点は [01_LocalStartup.md](./Reference/01_LocalStartup.md) を参照する。

------

## 完了判定

- `demo-bff` confidential client が作成されている
- `uvicorn main:app --app-dir apps/demo_bff --reload` でアプリが起動する
- `/login` から Keycloak のログイン画面へ遷移できる
- `alice` は `/me` 成功かつ `/admin` が `403` になる
- `bob` は `/me` 成功かつ `/admin` 成功になる
- logout 後は再認証が必要になる

------

## まとめ

今回の手順で確認したこと:

- `demo-bff` client を作成した
- FastAPI OIDC 検証アプリを起動した
- `/login` と `/auth/callback` による認可コードフローを確認した
- `/me` と `/admin` で認証・認可の差分を確認した
- logout を確認した

ここまでで、Keycloak の GUI で作成した設定を実際の Web アプリへ接続し、OIDC ログインと role ベース認可の最小構成を確認できた。  
次は [06_SetupFastAPI-BackendAPI.md](./06_SetupFastAPI-BackendAPI.md) を参照し、BFF と Backend API を分離して JWT 検証付き API 保護を確認する。

------

## 関連ドキュメント

- [04_SetupKeycloak.md](./04_SetupKeycloak.md) を参照
- [06_SetupFastAPI-BackendAPI.md](./06_SetupFastAPI-BackendAPI.md) を参照
- [07_SetupTokenValidationAndFailureCases.md](./07_SetupTokenValidationAndFailureCases.md) を参照
- [01_LocalStartup.md](./Reference/01_LocalStartup.md) を参照
- [02_AuthFlowArchitecture.md](./Reference/02_AuthFlowArchitecture.md) を参照
- [03_Troubleshooting.md](./Reference/03_Troubleshooting.md) を参照
- [main.py](../apps/demo_bff/main.py) を参照
