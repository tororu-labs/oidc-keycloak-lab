# 08 Public Client と PKCE

## 目的

このドキュメントは、public client と PKCE の仕組みを座学として整理するものである。

- public client と confidential client の違い
- PKCE の仕組み（`code_verifier` と `code_challenge` の関係）
- トークン保管場所の選択肢とトレードオフ
- BFF 構成と SPA 構成の対比

`docs/11_SetupNextJsSPAWithPKCE.md` のハンズオンと合わせて読むと理解しやすい。

------

## public client と confidential client の違い

Keycloak の client は「`client_secret` を安全に保持できるか」で 2 種類に分かれる。

| 種別 | 保管場所 | secret の有無 | 代表的な例 |
|------|---------|-------------|---------|
| confidential client | サーバ側 | 持てる | BFF（FastAPI）、バックエンドサービス |
| public client | ブラウザ / ネイティブアプリ | 持てない | SPA（Next.js）、モバイルアプリ |

**なぜ SPA は secret を持てないのか**

SPA のコードはブラウザにそのままダウンロードされる。DevTools を開けば誰でも中身を読める。仮に `client_secret` をコードに埋め込んでも、利用者が取り出して悪用できてしまう。

そのため、SPA では `client_secret` を使わない認可フローが必要になる。

------

## PKCE の仕組み

PKCE（Proof Key for Code Exchange、RFC 7636）は、認可コード横取り攻撃を防ぐための拡張である。

### なぜ認可コードが横取りされると困るのか

Authorization Code Flow では、Keycloak がブラウザに `code`（認可コード）を返す。このとき、OS やブラウザ拡張が `code` を傍受できてしまうことがある。`client_secret` があれば「`code` を持っていても secret を知らなければ token には換えられない」という防御になるが、public client には secret がない。

PKCE はこの問題を次の仕組みで解決する。

### PKCE のフロー

```
[SPA]                          [Keycloak]
  |                                |
  | 1. code_verifier を生成（ランダム文字列）
  |    code_challenge = SHA-256(code_verifier) を計算
  |                                |
  | 2. 認可リクエスト ─────────────→|
  |    code_challenge + method=S256 を送る
  |                                | Keycloak は code_challenge を記憶する
  | 3. ログイン画面（省略）          |
  |                                |
  | 4. callback: code を受け取る ←──|
  |                                |
  | 5. token リクエスト ────────────→|
  |    code + code_verifier を送る   |
  |                                | SHA-256(code_verifier) == 記憶した code_challenge
  |                                | → 一致すれば token を返す
  | 6. access_token を受け取る ←───|
```

### code_verifier と code_challenge の関係

| 値 | 生成タイミング | 送り先 | 保管場所 |
|---|---|---|---|
| `code_verifier` | ログイン開始時 | token endpoint（step 5） | sessionStorage |
| `code_challenge` | ログイン開始時（verifier から計算） | 認可リクエスト（step 2） | 送るだけ（保存不要） |

`code_verifier` は認可リクエストには含めない。token 交換のときに初めて提出する。Keycloak は「記憶しておいた `code_challenge` と、SHA-256(提出された `code_verifier`) が一致するか」だけを確認する。

攻撃者が `code` を横取りしても、`code_verifier` を知らなければ token には換えられない。

### `code_challenge_method`

`S256`（SHA-256）を使うこと。`plain` は `code_challenge == code_verifier` になるため安全ではない。Keycloak では realm 設定で `S256` を必須にできる。

------

## トークン保管場所の選択肢とトレードオフ

SPA で token を保管する場所として、主に 3 つの選択肢がある。

| 保管場所 | XSS への耐性 | ページリロード後 | 特徴 |
|---------|-----------|--------------|------|
| メモリ（React state） | 高い | 消える | JS からしか読めない。リロードで再ログインが必要 |
| sessionStorage | 低い | タブを閉じると消える | JS から読める。XSS で盗まれるリスクがある |
| localStorage | 低い | 残る | JS から読める。期限切れまで残り続ける |
| HttpOnly Cookie | 高い | 残る | JS から読めない。CSRF 対策が別途必要。SPA 単体では使いにくい |

**このラボでの選択**

`demo-web-spa` では access token をメモリ（React state）に保管する。XSS への耐性が最も高いが、ページリロードで消えてしまう。実運用では refresh token と組み合わせて、リロード後も再ログインなしで使い続けられるようにすることが多い（Phase 04 で扱う）。

**`code_verifier` だけは sessionStorage に置く理由**

Keycloak にリダイレクトして戻ってくるまでの間、ページのメモリは消える。`code_verifier` だけはリダイレクトをまたいで保持する必要があるため、sessionStorage を使う。ただし verifier は token 交換が終わったら即座に削除する。

------

## BFF 構成と SPA 構成の対比

| 項目 | BFF 構成（`demo-bff`） | SPA 構成（`demo-web-spa`） |
|------|----------------------|--------------------------|
| client の種別 | confidential | public |
| token の保管 | サーバ側 session | ブラウザ側メモリ |
| PKCE の必要性 | 任意（secret があるため） | 必須 |
| Backend API の呼び出し | BFF が Bearer を転送 | ブラウザが直接 Bearer を送る |
| CORS 設定 | 不要（同一オリジン想定） | Backend API 側で必要 |
| XSS への token 露出 | なし（token はサーバに留まる） | あり（JS から token を読める） |

どちらが「正しい」かは要件次第である。BFF 構成はセキュリティ面で有利だが、サーバ側の session 管理が必要になる。SPA 構成はインフラが単純だが、token の保管場所に慎重な設計が必要になる。

------

## 関連ドキュメント

- [11_SetupNextJsSPAWithPKCE.md](../11_SetupNextJsSPAWithPKCE.md)
- [05_TokenClaimsAndValidation.md](./05_TokenClaimsAndValidation.md)
- [04_ClientAndTokenRoles.md](./04_ClientAndTokenRoles.md)
