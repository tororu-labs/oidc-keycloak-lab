# Setup Next.js SPA + PKCE

## ここでのゴール

この手順では、SPA（シングルページアプリケーション）が PKCE を使って Keycloak と直接やりとりする構成を体験し、次の状態に到達することをゴールとする。

- Keycloak に `demo-web-spa`（public client）を登録できる
- `apps/demo_web_spa/` を起動し、`http://localhost:3000` でアクセスできる
- ブラウザから PKCE フローでログインでき、access token をメモリ内に保持できる
- ブラウザから Backend API（`http://localhost:8001/me`）を直接呼び出せる
- BFF 構成との違いを言語で説明できる

public client・PKCE・トークン保管のトレードオフは [08_PublicClientAndPKCE.md](./Reference/08_PublicClientAndPKCE.md) を参照する。  
用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。

------

## この手順では深く追わなくてよいこと

- **React / Next.js の内部動作**（hooks の仕組み、レンダリングサイクルなど）  
  → 「ボタンを押したら関数が呼ばれる」という動作を確認できれば十分
- **TypeScript の型ヒント**（`string | null` や `Promise<string>` など）  
  → 型チェッカー向けの注釈である。読み飛ばして問題ない
- **Web Crypto API の数学的な詳細**  
  → 「`crypto.subtle.digest("SHA-256", ...)` が SHA-256 ハッシュを計算する」だけ押さえる

------

## この手順で学ぶセキュリティの考え方

BFF 構成（`demo-bff`）では、token はサーバ側 session に留まり、ブラウザには届かなかった。SPA 構成では、token はブラウザのメモリ上に存在する。

この違いが生む問いは「ブラウザ上に token があるとき、どうやって守るか」である。

- PKCE は「認可コードを横取りされても token に換えられないようにする」仕組みである
- token をメモリに置くのは「JavaScript から読まれるリスクを sessionStorage / localStorage より下げる」選択である

どちらも完全な防御ではなく、要件に応じてトレードオフを選ぶ設計判断になる。

------

## 前提確認

この手順を始める前に、以下が完了していることを確認する。

- `docs/08_SetupAudienceValidation.md` の手順が完了している
- Keycloak が `http://localhost:8080` で起動している
- `apps/demo_api/` が `http://localhost:8001` で起動している
- Node.js（18 以上）がインストールされている

判定:

- `http://localhost:8001/` を開いて JSON が返ること
- `node -v` でバージョンが表示されること

------

## この手順の流れ

1. Keycloak に `demo-web-spa` public client を登録する
2. Audience Mapper を追加して `aud: demo-api` を token に付与する
3. Backend API に CORS を設定する
4. SPA を起動する
5. PKCE フローを体験する
6. Backend API を直接呼び出す
7. BFF 構成との挙動を比較する
8. 失敗例を再現する

------

## Step 1: Keycloak に `demo-web-spa` client を登録する

Keycloak 管理コンソール（`http://localhost:8080`）を開き、`lab` realm で作業する。

### Client の作成

1. 左メニューの **Clients** → **Create client** をクリックする
2. 以下を設定する

   | 項目 | 値 |
   |------|-----|
   | Client type | OpenID Connect |
   | Client ID | `demo-web-spa` |

3. **Next** をクリックする
4. **Capability config** 画面で以下を設定する

   | 項目 | 値 | 理由 |
   |------|-----|------|
   | Client authentication | OFF | public client は secret を持たない |
   | Standard flow | ON | Authorization Code Flow を使う |
   | Direct access grants | OFF | Password grant は使わない |

5. **Next** をクリックする
6. **Login settings** 画面で以下を設定する

   | 項目 | 値 |
   |------|-----|
   | Valid redirect URIs | `http://localhost:3000/*` |
   | Web origins | `http://localhost:3000` |

7. **Save** をクリックする

### PKCE の設定

1. 作成した `demo-web-spa` client の **Advanced** タブを開く
2. **Proof Key for Code Exchange Code Challenge Method** を `S256` に設定する
3. **Save** をクリックする

判定:

- `demo-web-spa` client が一覧に表示されている
- **Settings** タブで **Client authentication** が OFF になっている
- **Advanced** タブで Code Challenge Method が `S256` になっている

------

## Step 2: Audience Mapper を追加する

SPA は Backend API を直接呼び出すため、`demo-web-spa` client の token に `aud: demo-api` が含まれている必要がある。

1. `demo-web-spa` client の **Client scopes** タブを開く
2. `demo-web-spa-dedicated` をクリックする
3. **Add mapper** → **By configuration** → **Audience** を選択する
4. 以下を設定する

   | 項目 | 値 | 備考 |
   |------|-----|------|
   | Name | `audience-demo-api` | |
   | Included Custom Audience | `demo-api` | |
   | Add to ID token | OFF | デフォルトのまま |
   | Add to access token | ON | デフォルトのまま |
   | Add to lightweight access token | OFF | デフォルトのまま |
   | Add to token introspection | ON | デフォルトのまま |

5. **Save** をクリックする

補足:

- `Included Client Audience` は Keycloak に同名の client が登録されているときに使う項目である。`demo-api` は Keycloak の client として登録していないため、`Included Custom Audience` に文字列で `demo-api` を入力する。
- `Add to access token: ON` が本手順の目的（ブラウザから Bearer token で API を呼ぶ）に必要な設定である。その他のトグルはデフォルトから変更しなくてよい。

### Token Evaluate で確認する

1. `demo-web-spa` client の **Client scopes** タブ → **Evaluate** を開く
2. User に `alice` を選択する
3. **Generated access token** を確認し、`"aud": [..., "demo-api"]` が含まれていることを確認する

判定:

- Token Evaluate で `aud` に `demo-api` が入っている

------

## Step 3: Backend API に CORS を設定する

SPA はブラウザから直接 Backend API を呼び出す。ブラウザは異なるオリジン（`http://localhost:3000` → `http://localhost:8001`）へのリクエストを CORS ポリシーで制限するため、Backend API 側で許可設定が必要になる。

このラボでは、`apps/demo_api/main.py` に `CORSMiddleware` がすでに追加されている。

~~~python
# SPA（demo-web-spa）からのブラウザ直接アクセスを許可する。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)
~~~

`CORS_ALLOWED_ORIGINS` 環境変数で許可オリジンを設定する（デフォルトは `http://localhost:3000`）。

Backend API を次のコマンドで起動する（既に起動中の場合は再起動する）。

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export CORS_ALLOWED_ORIGINS=http://localhost:3000
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

判定:

- `curl -s -I -H "Origin: http://localhost:3000" http://localhost:8001/me | grep -i access-control` を実行して `Access-Control-Allow-Origin: http://localhost:3000` が返ること

------

## Step 4: SPA を起動する

### `.env.local` を作成する

~~~zsh
cp apps/demo_web_spa/.env.local.example apps/demo_web_spa/.env.local
~~~

中身を確認する。

~~~
NEXT_PUBLIC_KEYCLOAK_BASE_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=lab
NEXT_PUBLIC_OIDC_CLIENT_ID=demo-web-spa
NEXT_PUBLIC_APP_BASE_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_API_BASE_URL=http://localhost:8001
~~~

### 依存関係をインストールして起動する

新しいターミナルを開き、以下を実行する。SPA は起動したままにするため、以降の操作は別ターミナルで行う。

~~~zsh
cd apps/demo_web_spa
npm install
npm run dev
~~~

判定:

- `http://localhost:3000` を開き、「ログインしていません。」と表示されること

------

## Step 5: PKCE フローを体験する

### ログイン前に Web インスペクタを準備する

ボタンを押した瞬間に Keycloak へリダイレクトが始まるため、先に Web インスペクタを開いて準備しておく。

Safari で Web インスペクタを使うには「開発」メニューが必要である。初めて使う場合は先に有効化する。

- Safari の **設定（Cmd + ,）** → **詳細** タブ → **「メニューバーに"開発"メニューを表示」** にチェックを入れる

準備手順:

1. `http://localhost:3000` を開いた状態で Web インスペクタを開く（**Cmd + Option + I** または メニューバー **開発 → Web インスペクタを表示**）
2. **Network** タブを開き、左上の **「保持」アイコン（円矢印）** をクリックして Preserve log を有効にする
   - これを ON にしておかないと、ページ遷移時に Network の履歴が消える
3. **Storage** タブ → **Session Storage** → `http://localhost:3000` も開いておく

### ログインを試みる

4. 「Keycloak でログイン（PKCE）」ボタンをクリックする
5. ボタンを押した直後（リダイレクト前）に **Storage** タブ → **Session Storage** を確認する
   - `pkce_verifier` にランダムな文字列が入っていることを確認する（これが `code_verifier`）
   - 確認できたら Keycloak のログイン画面でそのまま続ける
6. `alice` でログインする
7. `http://localhost:3000/callback` に戻り、「認証処理中...」の後に `http://localhost:3000` にリダイレクトされる

補足: ボタンを押してから Keycloak 画面が表示されるまでに少し間がある。その間に Session Storage タブに切り替えると確認できる。タイミングが難しければ、ログイン後に「Session Storage から消えていること」だけ確認しても問題ない。

### ログイン後の状態を確認する

8. `http://localhost:3000` で「ログイン済み（access token をメモリ内に保持中）」と表示されていることを確認する
9. Web インスペクタ → **Storage** → **Session Storage** で `pkce_verifier` が消えていることを確認する（token 交換後に削除された）

### フローの内側を確認する

DevTools の **Network** タブで以下のリクエストを確認する（Preserve log を ON にしておいたので残っているはず）。

| # | URL | 方向 | 中身 |
|---|-----|------|-----|
| 1 | `http://localhost:8080/.../auth?code_challenge=...` | SPA → Keycloak | PKCE 認可リクエスト |
| 2 | `http://localhost:3000/callback?code=...` | Keycloak → SPA | 認可コードの受け取り |
| 3 | `http://localhost:8080/.../token` | SPA → Keycloak | `code` + `code_verifier` で token を取得 |

リクエスト 3 を選択して **Request** タブを開くと `code_verifier` が送られているのを確認できる。

判定:

- `http://localhost:3000` で「ログイン済み」と表示される
- Session Storage から `pkce_verifier` が消えている

------

## Step 6: Backend API を直接呼び出す

「Backend API (/me) を直接呼ぶ」ボタンをクリックする。

- ステータス `200` と、`alice` のプロフィール情報が表示されることを確認する
- Web インスペクタの **Network** タブで、リクエスト先が `http://localhost:8001/me` であることを確認する
  - リクエストを選択して **Request** タブを開き、`Authorization: Bearer eyJ...` が含まれていることを確認する
  - これは BFF を介さず、ブラウザが直接 Bearer token を送っていることを意味する

判定:

- `http://localhost:8001/me` が `200` を返す
- レスポンスに `alice` の情報が含まれている

------

## Step 7: BFF 構成との挙動を比較する

BFF（`http://localhost:8000`）と SPA（`http://localhost:3000`）を両方開いて比較する。

BFF がまだ起動していない場合は、別ターミナルで起動する。

~~~zsh
source .venv/bin/activate
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=lab
export OIDC_CLIENT_ID=demo-bff
export OIDC_CLIENT_SECRET='Keycloak で確認した demo-bff の client secret'
export APP_BASE_URL=http://localhost:8000
export BACKEND_API_BASE_URL=http://localhost:8001
export SESSION_SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn main:app --app-dir apps/demo_bff --host 127.0.0.1 --port 8000 --reload
~~~

| 確認ポイント | BFF（demo-bff） | SPA（demo-web-spa） |
|------------|----------------|-------------------|
| token の場所 | サーバ側 session | ブラウザのメモリ |
| Web インスペクタで token を見られるか | 見られない（Cookie の中に session ID のみ） | 見られる（Network タブの Authorization ヘッダー） |
| Backend API の呼び出し元 | サーバ（BFF から転送） | ブラウザ（直接 fetch） |
| ページをリロードしたとき | ログイン状態が維持される | ログインが消える（メモリが消えるため） |

ページをリロードして、SPA でログイン状態が失われることを確認する。

判定:

- SPA でリロード後に「ログインしていません。」と表示されること

------

## Step 8: 失敗例を再現する

### 失敗例 1: `code_challenge_method` の不一致

Keycloak の `demo-web-spa` client の **Advanced** タブを開き、**PKCE Code Challenge Method** を `plain` に変更してログインを試みる。

期待する見え方:

- `lib/pkce.ts` では常に `S256` を送っているため、Keycloak が認可リクエストを拒否する
- ブラウザのアドレスバーが `http://localhost:3000/callback?error=invalid_request` になる
- 画面に「認証エラー: invalid_request」と表示される

確認後、Keycloak の設定を `S256` に戻す。

### 失敗例 2: CORS 設定漏れで Backend API にアクセスできない

Backend API を CORS 設定なしで起動する（`CORS_ALLOWED_ORIGINS` 環境変数を外す）。

~~~zsh
uvicorn main:app --app-dir apps/demo_api --host 127.0.0.1 --port 8001 --reload
~~~

SPA でログインして「Backend API (/me) を直接呼ぶ」ボタンをクリックする。

期待する見え方:

- 画面に「API 呼び出し失敗: TypeError: Failed to fetch」と表示される
- Web インスペクタの **Console** に「Load failed」や「Cross-Origin request blocked」などの CORS エラーが表示される
- Web インスペクタの **Network** タブで `/me` リクエストが失敗している

確認後、`CORS_ALLOWED_ORIGINS=http://localhost:3000` を設定して Backend API を再起動する。

### 失敗例 3: `redirect_uri` 不一致

Keycloak の `demo-web-spa` client の **Settings** タブで **Valid Redirect URIs** を `http://localhost:3000/other` に変更する。

`http://localhost:3000` でログインを試みる。

期待する見え方:

- Keycloak がエラーページを表示する（`Invalid redirect_uri`）
- `http://localhost:3000/callback` への redirect が行われない

確認後、Valid Redirect URIs を `http://localhost:3000/*` に戻す。

------

## まとめ

この手順では以下を実施した。

- Keycloak に `demo-web-spa`（public client）を登録し、PKCE を `S256` で有効化した
- `demo-web-spa` の dedicated scope に Audience Mapper を追加して `aud: demo-api` を付与した
- Backend API に CORSMiddleware を追加して `http://localhost:3000` からのリクエストを許可した
- `apps/demo_web_spa/`（Next.js）を起動し、`http://localhost:3000` でアクセスできることを確認した
- PKCE フロー（verifier 生成 → challenge 送付 → code 受け取り → verifier で token 交換）を体験した
- ブラウザから Backend API を直接呼び出し、BFF を経由しない Bearer アクセスを確認した
- BFF 構成との挙動の違い（token の場所・CORS・リロード時の挙動）を比較した

次のステップ（Phase 04）では、この SPA に Refresh Token と Back-channel Logout を追加する。access token が切れたときに自動で再取得し、Keycloak 側でセッションを終了したときに SPA 側も即座に無効化される仕組みを実装する。

------

## 関連ドキュメント

- [Reference/08_PublicClientAndPKCE.md](./Reference/08_PublicClientAndPKCE.md)
- [Reference/04_ClientAndTokenRoles.md](./Reference/04_ClientAndTokenRoles.md)
- [Reference/05_TokenClaimsAndValidation.md](./Reference/05_TokenClaimsAndValidation.md)
- [08_SetupAudienceValidation.md](./08_SetupAudienceValidation.md)
