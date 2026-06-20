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

- `alice` でログインして `http://localhost:8000/api/me` が `200` を返す

------

## この手順の流れ

1. Keycloak の token 有効期限設定を確認する
2. access token 期限切れを体験する
3. refresh による自動更新を確認する
4. Keycloak に Back-Channel Logout URL を設定する
5. back-channel logout を体験する
6. 失敗例を再現する

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

## Step 2: access token 期限切れを体験する

access token の TTL を短くして、期限切れが起きることを確認する。

### Keycloak で TTL を変更する

1. **Realm settings → Tokens** タブを開く
2. **Access Token Lifespan** を `1 Minutes` に変更して **Save** をクリックする

### BFF と Backend API を起動する

~~~zsh
# ターミナル 1: Backend API
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export CORS_ALLOWED_ORIGINS=http://localhost:3000
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload

# ターミナル 2: BFF
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

### この手順でやること

TTL を短くすることで「access token がすぐに期限切れになる状態」を作る。BFF には refresh が実装済みなので、この状態で Step 3 に進む。

補足: refresh が実装されていない場合、1 分後に `/api/me` を開くと Backend API が `401` を返し、BFF がエラーをそのまま表示してしまう。今回はそれを自動で回避する実装を確認するのが目的。

------

## Step 3: refresh による自動更新を確認する

access token の TTL を短く設定した状態で、refresh が自動で動くことを確認する。

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

## Step 4: Keycloak に Back-Channel Logout URL を設定する

Keycloak がセッション終了を BFF に通知できるように、`demo-bff` client に Back-Channel Logout URL を設定する。

1. 左メニューの **Clients** を開く
2. `demo-bff` を選ぶ
3. **Settings** タブを開く
4. 以下を設定して **Save** をクリックする

| 設定項目 | 値 |
|---------|---|
| Backchannel logout URL | `http://localhost:8000/backchannel-logout` |
| Backchannel logout session required | ON |
| Backchannel logout revoke offline sessions | OFF |

判定:

- `demo-bff` の Settings に Backchannel logout URL が保存される

補足:

- **Backchannel logout session required** を ON にすると、logout token に `sid` claim が含まれる。BFF はこの `sid` を使って削除対象の session を特定する
- Keycloak（Docker コンテナ）から BFF（ホスト上の `localhost:8000`）に通知が届くには、Keycloak がホストの `localhost` を解決できる必要がある。Docker Desktop（Mac / Windows）を使っている場合は `host.docker.internal` が自動で解決されるが、`localhost` のままでも Docker Desktop では通ることが多い。通知が届かない場合は URL を `http://host.docker.internal:8000/backchannel-logout` に変えて試すこと（`docs/03_SetupDocker-Keycloak.md` 参照）

------

## Step 5: back-channel logout を体験する

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

## Step 6: 失敗例を再現する

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

### 失敗例 3: backchannel-logout URL 未設定で logout を試みる

目的:

Keycloak の **Backchannel logout URL** が設定されていない場合、session 強制終了が BFF に通知されないことを確認する。

再現方法:

1. `demo-bff` の Settings で **Backchannel logout URL** を空にして Save する
2. Keycloak の Sessions から `alice` の session を強制終了する
3. `http://localhost:8000/api/me` にアクセスする

期待する見え方:

- BFF の session が残ったままになるため、`/api/me` が引き続き `200` を返す
- BFF のログに back-channel 関連のログが出力されない

確認後、**Backchannel logout URL** を `http://localhost:8000/backchannel-logout` に戻す。

補足:

- back-channel logout は Keycloak と BFF の両方の設定が揃って初めて機能する
- URL が未設定の場合は Keycloak が通知を送らないため、BFF の session はアイドルタイムアウトまで残る

------

## まとめ

今回の手順で確認したこと:

- access token には有効期限があり、BFF は refresh token を使って自動更新する仕組みを持った
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
