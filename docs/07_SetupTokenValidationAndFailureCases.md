# Setup Token Validation And Failure Cases

## ここでのゴール

この手順では、BFF 構成での token 検証観点と代表的な失敗例を確認し、次の状態に到達することをゴールとする。

- OIDC ログインと Backend API 保護で使っている token 検証観点を整理できる
- `redirect_uri`、`client secret`、Backend API 停止などの失敗例を再現できる
- `backend_status`、`error_stage`、`uvicorn` ログを使って、どこで失敗したかを切り分けられる

必要な用語は [00_Glossary.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/00_Glossary.md) を参照する。  
横断的な切り分け観点や `error_stage` 一覧は [03_Troubleshooting.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/03_Troubleshooting.md) に整理した。

------

## 前提確認

この手順を始める前に、OIDC ログインと BFF -> Backend API の正常系が確認できていることを前提とする。

- `docs/05_SetupFastAPI-OIDCLogin.md` の正常系が完了している
- `docs/06_SetupFastAPI-BackendAPI.md` の正常系が完了している
- Keycloak、BFF、Backend API の起動方法が分かっている

判定:

- `alice` で `/me` に到達できる
- `bob` で `/api/admin-data` に到達できる

------

## この手順の流れ

この手順では、以下の流れで進める。

1. BFF 構成で見ておきたい token 検証観点を整理する
2. OIDC ログインまわりの失敗例を再現する
3. Backend API 呼び出しまわりの失敗例を再現する
4. `error_stage` と `uvicorn` ログを見比べて切り分ける

------

## この手順で見る token 検証観点

この手順で失敗系を確認するときは、次の値を意識して見ると理解しやすい。

- `iss`
  - どの realm が token を発行したか
- `exp`
  - token が期限切れか
- `aud`
  - その token が誰向けか
- `azp`
  - どの client が token を受け取ったか
- `realm_access.roles`
  - API 側の認可に使う role

補足:

- 今回の手順では、まず `redirect_uri`、`client secret`、downstream 到達性を中心に確認する
- `aud`、`iss`、`exp` の異常系は、この文書を起点に後で追加しやすいようにしている

------

## OIDC ログインまわりの失敗例

### 失敗例 1: Keycloak 停止

目的:

Keycloak が停止していると、OIDC ログインフローのどこで失敗するかが変わることを確認する。

再現方法:

- Keycloak を停止した状態で `/login` を試す
- または、ログイン途中や logout 前後で Keycloak を停止して挙動を確認する

期待する見え方:

- ブラウザで Keycloak へ遷移できない、または接続失敗になる
- タイミングによっては callback や logout 周辺で失敗する
- `uvicorn` ログでは `/login` のあとに進めない、または callback / logout 周辺で失敗する

補足:

- 失敗位置は Keycloak を停止したタイミングに依存する
- 学習用としては、「ログイン開始、callback、logout のどこかで失敗する」と理解できれば十分である

------

### 失敗例 2: `redirect_uri` 不一致

目的:

Keycloak が `redirect_uri` を厳密に確認しており、不一致の場合は認可開始時点で拒否することを確認する。

再現方法:

- FastAPI 側の `APP_BASE_URL` を、Keycloak に登録した redirect URI と一致しない値へ変更する

例:

~~~zsh
export APP_BASE_URL=http://127.0.0.1:8000
~~~

期待する見え方:

- Keycloak 画面で `Invalid parameter: redirect_uri` が表示される
- `uvicorn` ログには `/login` は残るが、`/auth/callback` は発生しない

補足:

- これは token 交換エラーではなく、認可開始時点での不一致エラーである
- Keycloak は `Valid redirect URIs` と一致するかを確認している

------

### 失敗例 3: `client secret` 不一致

目的:

`client secret` が一致しない場合、ログイン画面までは進めても callback 後の認可処理で失敗することを確認する。

再現方法:

- FastAPI 側の `OIDC_CLIENT_SECRET` を、Keycloak の `demo-bff` client secret と異なる値へ変更する

例:

~~~zsh
export APP_BASE_URL=http://localhost:8000
export OIDC_CLIENT_SECRET='本来のsecretを少し変えた値'
~~~

期待する見え方:

- `/auth/callback` 後に `OIDC callback エラー` が表示される
- `error='unauthorized_client'` や `Invalid client credentials` を確認できることがある
- `uvicorn` ログには `/auth/callback` へのアクセスや `400` が残ることがある

補足:

- `/login` と Keycloak のログイン画面までは進める
- callback 後の token 交換または認可処理で、client 認証に失敗している

------

## Backend API 呼び出しまわりの失敗例

### 失敗例 1: Backend API 停止

目的:

Backend API に到達できないとき、BFF 側でどのように失敗が見えるかを確認する。

再現方法:

- Backend API を停止した状態で `http://localhost:8000/api/me` または `http://localhost:8000/api/admin-data` を開く

期待する見え方:

- BFF 側で接続失敗が返る
- `error_stage` が `backend_connection` になる
- `backend_url` に `http://localhost:8001/...` が含まれる
- BFF 側の `uvicorn` ログでは `stage=bff_proxy_connection_error` を確認できる

補足:

- この失敗は認証・認可エラーではなく、downstream 接続失敗である

------

## ログと `error_stage` の見方

失敗系を確認するときは、次の 3 つを見比べる。

1. ブラウザ画面
2. BFF の `uvicorn` ログ
3. Backend API の `uvicorn` ログ

まず見る順番:

1. `backend_status`
2. `error_stage`
3. 画面のエラーメッセージ
4. `uvicorn` ログの `stage=...`

補足:

- `error_stage` の意味一覧は [03_Troubleshooting.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/03_Troubleshooting.md) を参照する
- 必要なら `?raw=1` を付けて raw JSON を直接確認できる

------

## 実行コマンド一覧

### 起動コマンド

~~~zsh
# BFF
uvicorn main:app --app-dir apps/demo_bff --reload

# Backend API
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

### 失敗例再現用の変更例

~~~zsh
# redirect_uri 不一致
export APP_BASE_URL=http://127.0.0.1:8000

# client secret 不一致
export OIDC_CLIENT_SECRET='本来のsecretを少し変えた値'
~~~

------

## 完了判定

- OIDC ログインまわりの失敗例を再現できる
- Backend API 停止時の見え方を確認できる
- `backend_status`、`error_stage`、`uvicorn` ログを使って失敗位置を説明できる

------

## まとめ

今回の手順で確認したこと:

- BFF 構成で意識したい token 検証観点を整理した
- OIDC ログインまわりの代表的な失敗例を再現した
- Backend API 停止時の失敗を再現した
- `error_stage` とログを使った切り分けの入口を確認した

ここまでで、正常系だけでは見えにくかった失敗位置の違いを確認できた。  
次は `aud` や token 異常系を増やし、Backend API 側の token 検証観点をさらに深める。

------

## 関連ドキュメント

- [05_SetupFastAPI-OIDCLogin.md](./05_SetupFastAPI-OIDCLogin.md) を参照
- [06_SetupFastAPI-BackendAPI.md](./06_SetupFastAPI-BackendAPI.md) を参照
- [03_Troubleshooting.md](./Reference/03_Troubleshooting.md) を参照
- [04_ClientAndTokenRoles.md](./Reference/04_ClientAndTokenRoles.md) を参照
