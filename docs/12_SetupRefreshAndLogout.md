# Setup Refresh Token と Back-channel Logout

## ここでのゴール

この手順では、token のライフサイクル管理を BFF に追加し、次の状態に到達することをゴールとする。

- access token が期限切れになっても、refresh token を使って自動で更新し、ユーザーを再ログインさせずにアクセスを継続できる
- Keycloak の管理コンソールからユーザーの session を強制終了すると、back-channel 経由で BFF の session も即座に無効化される
- logout token を改ざんすると検証で弾かれることを確認できる

必要な用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。

------

## 背景

`docs/11_SetupNextJsSPAWithPKCE.md` まで、BFF は access token を session に保存して Backend API へ転送してきた。しかし access token には有効期限（デフォルトで数分〜1時間）があり、期限切れになると Backend API が `401` を返す。

`11` の手順で SPA ではページリロードでログインが消えることを体験した。BFF 構成でも token が切れると同じ問題が起きる。refresh token を使うことで、ユーザーを再ログインさせずにアクセスを継続できる。

また、企業環境では「あるアプリでログアウトしたら他のアプリも自動でログアウト」（Single Logout）が求められる。back-channel logout は Keycloak がサーバー間で直接ログアウト通知を送る仕組みで、ブラウザが閉じられていても確実に機能する。

この手順では、次の 2 つを組み合わせて token ライフサイクル管理を完成させる。

- Refresh Token による自動 access token 更新
- Back-channel Logout による server-side session 強制削除

------

## 前提確認

この手順を始める前に、以下が完了していることを確認する。

- `docs/08_SetupAudienceValidation.md` の手順が完了している
- `docs/11_SetupNextJsSPAWithPKCE.md` の手順が完了している（BFF に refresh_token 保管の実装が含まれている）
- `demo-bff` client が `http://localhost:8080` の `lab` realm に存在する
- BFF と Backend API を起動してログインできる状態になっている

判定:

- `alice` でログインして `http://localhost:8080/api/me` が `200` を返す

------

## この手順の流れ

1. Keycloak の token 有効期限設定を確認する
2. SPA で access token 期限切れを体験する
3. BFF を加えて refresh による自動更新を確認する
4. URL 未設定のまま logout を試み、BFF に届かないことを確認する
5. Keycloak に Back-Channel Logout URL を設定する
6. back-channel logout を体験する
7. 失敗例を再現する

------

## Step 1: Keycloak の token 有効期限設定を確認する

Keycloak の管理コンソールで、token の TTL 設定を確認する。

1. `http://localhost:8080` の管理コンソールを開く
2. 左上で `lab` realm を選ぶ
3. 左メニューの **Realm settings** を開く
4. **Tokens** タブを開く

以下の設定を確認する。

| 設定項目 | デフォルト値 | 意味 |
|---------|------------|------|
| Access Token Lifespan | 5 minutes | access token の有効期限 |
| Refresh Token | 30 minutes（SSO Session Idle） | refresh token が有効な期間 |
| SSO Session Idle | 30 minutes | アイドル状態で session が切れるまでの時間 |
| SSO Session Max | 10 hours | session の最大継続時間 |

判定:

- **Tokens** タブで各 TTL の値が表示される

------

## Step 2: SPA で access token 期限切れを体験する

refresh token を持たない SPA で access token が切れると何が起きるかを確認する。

### Keycloak で TTL を変更する

1. **Realm settings → Tokens** タブを開く
2. **Access Token Lifespan** を `1 Minutes` に変更して **Save** をクリックする

### Backend API と SPA を起動する

~~~zsh
# ターミナル 1: Backend API
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export CORS_ALLOWED_ORIGINS=http://localhost:3000
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload

# ターミナル 2: SPA
cd apps/demo_web_spa
npm run dev
~~~

### 操作手順

1. `http://localhost:3000` で `alice` としてログインする
2. 1 分（TTL）が経過するまで待つ
3. API を呼び出す操作（`/api/me` に相当する画面操作）を行う

期待する見え方:

- 画面に `401` エラーが表示される
- SPA はユーザーに再ログインを要求する、またはエラー画面を表示する

判定:

- 1 分後に SPA が `401` エラーを表示する

------

## Step 3: BFF を加えて refresh による自動更新を確認する

BFF を追加することで、同じ TTL 設定でも refresh が自動で動くことを確認する。

### BFF を起動する

~~~zsh
# ターミナル 3: BFF（ターミナル 1・2 はそのまま）
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloak で確認した demo-bff の client secret'
export APP_BASE_URL=http://localhost:8000
export BACKEND_API_BASE_URL=http://localhost:8001
export SESSION_SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn main:app --app-dir apps/demo_bff --reload
~~~

### 操作手順

1. `http://localhost:8000` で `alice` としてログインする
2. 1 分（TTL）が経過するまで待つ
3. `http://localhost:8000/api/me` にアクセスする

期待する見え方:

- 再ログインを促されることなく、`200` のレスポンスが返る
- BFF の `uvicorn` ログに以下が出力される

~~~text
stage=bff_token_refresh_start user=alice
stage=bff_token_refresh_success user=alice
stage=bff_proxy_response ... backend_status=200 ...
~~~

判定:

- 1 分後に `/api/me` が `200` を返す
- BFF ログに `stage=bff_token_refresh_success` が出力される

補足:

- BFF は access token の `exp` claim を確認し、期限切れの 30 秒前から refresh を試みる
- refresh token が期限切れの場合は、session が削除されてログイン画面へリダイレクトされる
- 確認が終わったら、Keycloak の **Access Token Lifespan** を `5 Minutes` に戻す

------

## Step 4: URL 未設定のまま logout を試み、BFF に届かないことを確認する

Keycloak の Back-Channel Logout URL を設定しないまま session を強制終了し、BFF の session が残り続けることを確認する。

### 操作手順

1. BFF が起動している状態で `alice` でログインする
2. `http://localhost:8000/api/me` にアクセスし、`200` が返ることを確認する
3. Keycloak の管理コンソールを開く
4. 左メニューの **Sessions** を開く
5. 一覧から `alice` の session を見つけ、**Sign out** をクリックする
6. `http://localhost:8000/api/me` に再度アクセスする

期待する見え方:

- BFF の session が残ったままになるため、`/api/me` が引き続き `200` を返す
- BFF のログに back-channel 関連のログが出力されない

判定:

- Keycloak で session を強制終了しても、BFF の session が消えない

補足:

- back-channel logout は Keycloak と BFF の両方の設定が揃って初めて機能する
- URL が未設定の場合は Keycloak が通知を送らないため、BFF の session はアイドルタイムアウトまで残る
- この動作を確認したら、次の Step で URL を設定して解決する

------

## Step 5: Keycloak に Back-Channel Logout URL を設定する

Keycloak がセッション終了を BFF に通知できるように、`demo-bff` client に Back-Channel Logout URL を設定する。

1. 左メニューの **Clients** を開く
2. `demo-bff` を選ぶ
3. **Settings** タブを開く
4. 以下を設定して **Save** をクリックする

| 設定項目 | 値 |
|---------|---|
| Front channel logout | OFF |
| Backchannel logout URL | `http://host.docker.internal:8000/backchannel-logout` |
| Backchannel logout session required | ON |
| Backchannel logout revoke offline sessions | OFF |

判定:

- `demo-bff` の Settings に Backchannel logout URL が保存される

補足:

- **Front channel logout を OFF にする**。ON のままだと back-channel logout が使われず、通知が BFF に届かない
- **Backchannel logout session required** を ON にすると、logout token に `sid` claim が含まれる。BFF はこの `sid` を使って削除対象の session を特定する
- `host.docker.internal` は Docker Desktop（Mac / Windows）でホストマシンを指す特別なホスト名。Linux Docker の場合は Docker bridge の gateway IP（`ip route | grep default` で確認）を使う

------

## Step 6: back-channel logout を体験する

Keycloak の管理コンソールからユーザーの session を強制終了し、BFF の session も同時に無効化されることを確認する。

### 手順

1. BFF が起動している状態で `alice` でログインする
2. `http://localhost:8000/api/me` にアクセスし、`200` が返ることを確認する
3. Keycloak の管理コンソールを開く
4. 左メニューの **Sessions** を開く
5. 一覧から `alice` の session を見つけ、**Sign out** （または **Logout all sessions**）をクリックする
6. `http://localhost:8000/api/me` に再度アクセスする

期待する見え方:

- `/api/me` へのアクセスがログイン画面にリダイレクトされる
- BFF の `uvicorn` ログに以下が出力される

~~~text
stage=backchannel_logout_success keycloak_sid=xxx... user=alice
~~~

判定:

- Keycloak での session 強制終了後、BFF でも即座にログイン状態が解除される
- BFF ログに `stage=backchannel_logout_success` が出力される

------

## Step 7: 失敗例を再現する

### 失敗例 1: refresh token が期限切れ

目的:

refresh token の有効期限が切れると、refresh が失敗して session が削除されることを確認する。

再現方法:

1. Keycloak の **Realm settings → Tokens** タブで **SSO Session Idle** を `1 Minutes` に変更する
2. `alice` でログインする
3. 1 分以上、BFF にアクセスしない（ブラウザを操作しない）
4. `http://localhost:8000/api/me` にアクセスする

期待する見え方:

- ログイン画面にリダイレクトされる
- BFF のログに `stage=bff_token_refresh_error reason=refresh_failed` が出力される

確認後、**SSO Session Idle** を `30 Minutes` に戻す。

補足:

- SSO Session Idle が切れると Keycloak 側の session が削除され、refresh token が無効になる
- BFF は refresh 失敗時に session を削除してログイン画面にリダイレクトする

------

### 失敗例 2: logout token の改ざん

目的:

logout token の署名が不正な場合、back-channel logout が `400` で拒否されることを確認する。

再現方法:

~~~zsh
# 改ざんした logout token を BFF に送る（ペイロード部分に "fake" を入れる）
curl -X POST http://localhost:8000/backchannel-logout \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "logout_token=eyJhbGciOiJSUzI1NiJ9.ZmFrZS1wYXlsb2Fk.invalidsignature"
~~~

期待する見え方:

- `400` が返る
- BFF のログに `stage=backchannel_logout_error reason=invalid_token` が出力される

補足:

- BFF は Keycloak の JWKS（`/protocol/openid-connect/certs`）を取得して署名を検証する
- 署名が不正な token はここで弾かれるため、外部から session を削除させることはできない

------

## まとめ

今回の手順で確認したこと:

- refresh token を持たない SPA では、access token 期限切れで即座に `401` になることを確認した
- BFF に refresh token を持たせることで、ユーザーを再ログインさせずに自動更新できることを確認した
- refresh token も期限切れになると session が削除されてログイン画面に戻ることを確認した
- Keycloak の back-channel logout により、サーバー間で直接セッション無効化が通知されることを体験した
- logout token の署名検証により、外部から session を不正に削除させることができないことを確認した

ここまでで、BFF が token のライフサイクルを適切に管理できる状態になった。
次は OpenTelemetry による認証フローの可視化（Phase 05）に進む。

------

## 関連ドキュメント

- [11_SetupNextJsSPAWithPKCE.md](./11_SetupNextJsSPAWithPKCE.md) — SPA 構成との比較
- [08_SetupAudienceValidation.md](./08_SetupAudienceValidation.md) — Backend API の token 検証
- [Reference/08_PublicClientAndPKCE.md](./Reference/08_PublicClientAndPKCE.md) — refresh / logout の座学整理
- [Reference/00_Glossary.md](./Reference/00_Glossary.md) — 用語集
