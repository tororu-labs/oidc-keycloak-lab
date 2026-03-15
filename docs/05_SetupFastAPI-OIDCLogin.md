# Setup FastAPI OIDC Login

## 目的

このドキュメントは、IAM Study Lab の次の段階として、FastAPI を使って Keycloak の OIDC ログインを実アプリから利用する最小ハンズオンを記録するものである。  
主な目的は以下の通り。

- Keycloak に `demo-bff` client を追加し、FastAPI から認可コードフローを開始できるようにする
- FastAPI が `/login` と `/auth/callback` を通じて token を受け取れるようにする
- session を使ってログイン状態を保持し、`/me` と `/admin` で認証・認可結果を確認できるようにする
- `alice` と `bob` の role 差分がアプリ側の挙動にどう反映されるかを確認する

### 用語

- Authorization Code Flow: ブラウザを使って IdP にログインし、認可コードを経由して token を取得する OIDC / OAuth 2.0 の基本フロー
- callback: IdP が認可コードを返すために、アプリ側で待ち受ける URL
- confidential client: client secret を持ち、サーバ側で安全に token を扱う前提の client
- session: アプリがログイン状態を保持するための仕組み
- BFF: Browser と backend の間に立ち、token をブラウザへ直接渡さずに扱う構成パターン

------

## 実施概要

今回のセットアップでは、以下の流れで作業を進める。

1. Keycloak で `demo-bff` client を作成する
2. FastAPI アプリの依存関係をインストールする
3. 環境変数を設定してアプリを起動する
4. `/login` から Keycloak へログインし、`/me` と `/admin` を確認する
5. `alice` と `bob` の role 差分、および logout 後の状態を確認する

------

## 前提確認

この手順を始める前に、Keycloak の GUI セットアップが完了していることを確認する。  
具体的には、以下を満たしていることを前提とする。

- `lab` realm が存在する
- `alice` と `bob` の user が存在する
- `viewer` と `admin` の realm role が存在する
- Keycloak が `http://localhost:8080` で起動している

### 前提確認時の状態

- Keycloak 管理コンソールへログインできる
- `docs/04_SetupKeycloak.md` の手順が完了している

### 前提確認の判定

- `http://localhost:8080` の管理コンソールへ入れる
- `lab` realm の `Users` と `Realm roles` を確認できる

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

### `demo-bff` Client の作成の補足

- ここではブラウザから直接 token を扱わせず、FastAPI 側で token 交換を行うため confidential client を使う
- `redirect URI` は Keycloak が認可コードを返してよい URL の制限として必要になる
- `post logout redirect URI` は Keycloak 側 logout 後に戻る先として利用する

### `demo-bff` Client の作成完了時の状態

Keycloak は `demo-bff` を「FastAPI 側の OIDC client」として認識し、認可コードを `http://localhost:8000/auth/callback` へ返せる状態になった。

### `demo-bff` Client の作成の判定

- `Clients` 一覧に `demo-bff` が存在する
- `Client authentication` が `ON` である
- `Valid redirect URIs` に `http://localhost:8000/auth/callback` が設定されている
- `Credentials` タブで secret を確認できる

------

## FastAPI アプリの構成

今回追加したアプリは `apps/demo_bff/` に置いてある。  
主なファイルは以下。

- `main.py`
  - FastAPI 本体
  - `/login`、`/auth/callback`、`/me`、`/admin`、`/logout` を提供する
- `requirements.txt`
  - 実行に必要な依存関係
- `.env.example`
  - 必要な環境変数の見本

### FastAPI アプリの構成の補足

- このアプリは案Aの最小構成であり、FastAPI が OIDC client と簡易 BFF を兼ねる
- token は FastAPI が受け取り、ブラウザとは session cookie ベースでやり取りする
- session store は最小実装としてアプリ内メモリを使うため、アプリ再起動時にはログイン状態が消える

------

## 依存関係のインストール

プロジェクトルートで仮想環境を有効化し、依存関係をインストールする。

~~~zsh
source .venv/bin/activate
python -m pip install -r apps/demo_bff/requirements.txt
~~~

### 依存関係のインストールの補足

- `fastapi`: アプリ本体
- `uvicorn`: 開発用サーバ
- `authlib`: OIDC / OAuth 2.0 client 処理
- `httpx`: Authlib の HTTP 通信に利用
- `itsdangerous`: session cookie の署名に利用

### 依存関係のインストールの判定

- `python -m pip install -r apps/demo_bff/requirements.txt` が成功する
- `python -m pip show fastapi authlib uvicorn` で導入を確認できる

------

## 環境変数の設定

`.env.example` を参考に、実行用の環境変数を設定する。  
ここでは手動で `export` する方法を記載する。

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloakで確認したclient secret'
export APP_BASE_URL=http://localhost:8000
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

### 環境変数の設定の補足

- `OIDC_CLIENT_SECRET` は Keycloak の `Credentials` タブで確認した値を使う
- `SESSION_SECRET` は Cookie 署名用であり、`OIDC_CLIENT_SECRET` とは別物である
- `KEYCLOAK_REALM=lab` により、既存の `lab` realm をそのまま再利用する

### 環境変数の設定完了時の状態

FastAPI アプリが Keycloak の discovery endpoint と `demo-bff` client を使って認可コードフローを開始できる設定が整った。

------

## FastAPI アプリの起動

環境変数を設定した状態で、開発サーバを起動する。

~~~zsh
source .venv/bin/activate
uvicorn main:app --app-dir apps/demo_bff --reload
~~~

ブラウザで `http://localhost:8000` を開くと、未ログイン状態のトップページが表示される。

### FastAPI アプリ起動の判定

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

1. logout する
2. 再度 `Keycloak でログイン` を押す
3. `bob` の資格情報でログインする
4. `/me` で `preferred_username` が `bob` であることを確認する
5. role 一覧に `admin` が含まれることを確認する
6. `/admin` を開き、アクセス成功となることを確認する

### ログインフロー確認の補足

- `/me` は「誰としてログインしたか」を見る場所である
- `/admin` は「何ができるか」を見る場所である
- ここで `alice` はログインできても `/admin` には入れないため、認証と認可の違いが分かる

### ログインフロー確認の判定

- `alice` は `/me` へ到達できる
- `alice` は `/admin` で `403` になる
- `bob` は `/me` へ到達できる
- `bob` は `/admin` へ到達できる

------

## Logout と失敗系の確認

### Logout の確認

トップページまたはログイン済み画面から `ログアウト` を実行する。  
FastAPI はローカル session を削除し、その後 Keycloak の logout endpoint へ遷移する。

判定:

- logout 後にトップページへ戻る
- `/me` または `/admin` を開くと再ログインが必要になる

### Keycloak 停止時の確認

Keycloak を停止した状態で `/auth/callback` の token 交換が必要になると、FastAPI はエラーページを表示する。

期待する見え方:

- `Token 交換エラー` として画面に表示される
- Keycloak 停止、client secret 相違、redirect URI 不一致などの切り分けヒントが表示される

------

## 本ドキュメントで完了したこと

以下が完了した状態になった。

- Keycloak に `demo-bff` client を作成
- FastAPI OIDC 検証アプリを追加
- `/login` と `/auth/callback` による認可コードフローを確認
- session を使ったログイン状態の保持を確認
- `/me` と `/admin` による認証・認可の差分確認
- logout 後に再認証が必要になることを確認

つまり、Keycloak の GUI 設定を実際の Web アプリへ接続し、OIDC ログインと role ベース認可の最小構成を再現できる状態になった。

------

## 実行コマンド一覧

### 依存関係と起動

~~~zsh
source .venv/bin/activate # 仮想環境を有効化
python -m pip install -r apps/demo_bff/requirements.txt # 依存関係を導入
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

------

## 完了判定

以下を満たしたため、FastAPI を使った最小 OIDC ログイン検証は完了とする。

- `demo-bff` confidential client が作成されている
- `uvicorn main:app --app-dir apps/demo_bff --reload` でアプリが起動する
- `/login` から Keycloak のログイン画面へ遷移できる
- `alice` は `/me` 成功かつ `/admin` が `403` になる
- `bob` は `/me` 成功かつ `/admin` 成功になる
- logout 後は再認証が必要になる

------

## 関連ドキュメント

- [docs/04_SetupKeycloak.md](./04_SetupKeycloak.md)
- [scratch/OIDC最小ハンズオン理解メモ.md](../scratch/OIDC最小ハンズオン理解メモ.md)
- [apps/demo_bff/main.py](../apps/demo_bff/main.py)

------

## まとめ

今回のセットアップで、Keycloak の GUI で作成した `realm / user / role / client` を FastAPI から実際に利用し、OIDC ログインと session 管理、role ベース認可の最小構成を確認できた。  
今後はこの構成を土台にして、BFF と Backend API の分離、JWT 検証、Next.js 連携へ進めることができる。
