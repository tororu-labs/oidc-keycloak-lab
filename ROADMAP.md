# iam-lab-study ROADMAP

> 作成日: 2026-05-17
> 目的: docs/ と docs/Reference/ の追加計画を、フェーズ単位で着手・完了判定できる形に整理する
> 使い方: Claude Code に「Phase NN を実装してほしい」と指示する。1フェーズ単位で進め、完了判定を満たしてから次へ移る。

---

## このロードマップの読み方

- 各 Phase は **1つのハンズオン docs と 0〜1つの座学 Reference** で構成される
- Phase は **依存関係順** に並んでいる。原則として前の Phase の完了判定を満たしてから次へ進む
- 各 Phase には以下を記載する
  - **学ぶ動機**: なぜこの Phase が必要か
  - **実装すると何が分かるか**: 実装を通じて獲得する理解
  - **作成するファイル**: 新規作成または更新するファイル
  - **主な扱う内容**: 中で扱うトピックの一覧
  - **想定する失敗例**: 学習価値の高い失敗ケース
  - **完了判定**: この Phase を「完了」と見なす条件

---

## 全体マップ

### docs/ と docs/Reference/ の対応関係

```
docs/                                  docs/Reference/
────────────────────────────────────────────────────────────────────
                                       00_Glossary.md          ← 全体共通
                                       01_LocalStartup.md      ← 全体共通

03_SetupDocker-Keycloak ─────┐
04_SetupKeycloak ────────────┤
05_SetupFastAPI-OIDCLogin ───┼──→ 02_AuthFlowArchitecture
06_SetupFastAPI-BackendAPI ──┘     04_ClientAndTokenRoles

07_SetupTokenValidation ─────────→ 03_Troubleshooting

08_SetupAudienceValidation ──┐
                             ├──→ 05_TokenClaimsAndValidation  ← 新規
09_SetupClientScopeAndMapper ┘     06_ClientScopeAndMapperTypes ← 新規

10_SetupJWTEdgeCaseTests ────────→ 05_TokenClaimsAndValidation  ← 再利用

11_SetupSecurityAuditAgent ──────→ 07_AuditAndObservability    ← 新規
12_SetupOTelInstrumentation ─────↗

13_SetupMCPServer ───────────────→ 08_MCPAuthorizationFlow     ← 新規

14_SetupNextJsSPAWithPKCE ───┐
                             ├──→ 09_PublicClientAndPKCE       ← 新規
15_SetupRefreshAndLogout ────┘
```

### Phase 一覧

| Phase | 種別 | 対象ファイル | ステータス |
|-------|------|-------------|----------|
| Phase 00 | Reference 切り出し | `Reference/05_TokenClaimsAndValidation.md` | 🔲 未着手 |
| Phase 01 | ハンズオン + Reference | `09_SetupClientScopeAndMapper.md` + `Reference/06_ClientScopeAndMapperTypes.md` | 🔲 未着手 |
| Phase 02 | ハンズオン | `10_SetupJWTEdgeCaseTests.md` | 🔲 未着手 |
| Phase 03 | ハンズオン + Reference | `11_SetupSecurityAuditAgent.md` + `Reference/07_AuditAndObservability.md` | 🔲 未着手 |
| Phase 04 | ハンズオン | `12_SetupOTelInstrumentation.md` | 🔲 未着手 |
| Phase 05 | ハンズオン + Reference | `13_SetupMCPServer.md` + `Reference/08_MCPAuthorizationFlow.md` | 🔲 未着手 |
| Phase 06 | ハンズオン + Reference | `14_SetupNextJsSPAWithPKCE.md` + `Reference/09_PublicClientAndPKCE.md` | 🔲 未着手 |
| Phase 07 | ハンズオン | `15_SetupRefreshAndLogout.md` | 🔲 未着手 |

---

## Phase 00: 既存 docs/08 の座学を Reference に切り出す

### 学ぶ動機

`docs/08_SetupAudienceValidation.md` で扱った内容には、ハンズオンの手順と座学的な解説（claim の意味、検証の順序、Authlib の仕組みなど）が混ざっている。これを Reference に切り出すことで、後の Phase 02（JWT エッジケーステスト）でも再利用できる座学資産になる。

### 実装すると何が分かるか

- claim 検証は「署名 → `iss` → `exp` → `aud`」の順序で並べると、各検証の役割が明確になる
- `aud` と `azp` の使い分けは、token 設計の中核的なポイント
- Authlib の `claims_options` が裏で何をしているかを言語化できる

### 作成するファイル

- 新規: `docs/Reference/05_TokenClaimsAndValidation.md`

### 主な扱う内容

- token に含まれる代表的な claim（`iss` / `sub` / `aud` / `azp` / `exp` / `iat` / `realm_access.roles`）の意味と例
- Backend API が検証すべき claim の順序（署名 → `iss` → `exp` → `aud`）と各検証の役割
- `aud` と `azp` の使い分け
  - `aud`: token を受け取るべきサービス（誰向け）
  - `azp`: token を要求した client（誰が要求したか）
- Authlib の `claims_options` の仕組み
  - `essential` と `value` の意味
  - 例外型（`InvalidClaimError`, `ExpiredTokenError`, `InvalidSignatureError` など）の対応表

### 完了判定

- `docs/Reference/05_TokenClaimsAndValidation.md` が作成されている
- 既存の `docs/08_SetupAudienceValidation.md` から、新 Reference へのリンクが追加されている
- `docs/Reference/04_ClientAndTokenRoles.md` の「Access Token で API が見ているもの」セクションから、新 Reference への参照リンクが追加されている

---

## Phase 01: Client Scope と Mapper の体系整理

### 学ぶ動機

`docs/08` で Audience Mapper を1つ追加して、token の中身を Keycloak 側で操作できることを体験した。しかし mapper には他にも多数あり、client scope という箱の仕組みもある。

実務では「token に独自の claim を入れたい」「scope と role の違い」「default scope と optional scope の使い分け」が頻繁に問われる。この Phase でその知識を体系化する。

### 実装すると何が分かるか

- dedicated scope（client 専用）と shared scope（複数 client で使い回し）の違い
- default scope（黙って付く）と optional scope（明示要求が必要）の使い分け
- 各種 mapper の役割と使いどころ
- scope ベースの認可の入り口

### 作成するファイル

- 新規: `docs/09_SetupClientScopeAndMapper.md`
- 新規: `docs/Reference/06_ClientScopeAndMapperTypes.md`

### 主な扱う内容（ハンズオン）

- 共通の shared client scope を作成して `demo-bff` に割り当てる
- User Property Mapper を追加して、token に独自 claim を出す
- Hardcoded Claim Mapper で固定値を埋めてみる
- Role Name Mapper で role 名を変換する
- optional scope を作成し、scope パラメータで明示要求する流れを確認する
- Token Evaluate で各 mapper の効果を確認する

### 主な扱う内容（Reference）

- client scope の正体（mapper をまとめる箱）
- dedicated scope vs shared scope の違いと再利用パターン
- default scope vs optional scope の動作の違い
- 主要な mapper 種別カタログ（Audience / User Property / Hardcoded Claim / Role Name / Group Membership など）
- OAuth2 の scope と Keycloak の role の関係

### 想定する失敗例

- scope assign 忘れで claim が出ない
- optional scope を `scope` パラメータで要求しなかった場合の挙動
- shared scope と dedicated scope を取り違えて他の client にも影響が出るケース

### 完了判定

- `docs/09_SetupClientScopeAndMapper.md` が作成され、既存の docs と同じ形式（ここでのゴール / この手順の流れ / 実施手順 / 完了判定 / まとめ）に従っている
- `docs/Reference/06_ClientScopeAndMapperTypes.md` が作成されている
- ハンズオンを実行すると、Token Evaluate で追加した mapper の効果が確認できる
- 失敗例を再現すると、期待した挙動になることが確認できる

---

## Phase 02: JWT エッジケーステスト

### 学ぶ動機

`docs/08` までで実装した JWT 検証ロジック（署名・`iss`・`exp`・`aud`）は、正常系と数個の失敗例でしか検証されていない。`alg=none` 攻撃や `kid` 不正のような攻撃シナリオは、ブラウザ操作では再現できない。

pytest で異常系を意図的に作って検証することで、「実装した」だけでなく「異常系も押さえた」と説明できる状態を作る。

### 実装すると何が分かるか

- 「ライブラリが暗黙で処理してくれる部分」と「自分のコードが責任を持つ部分」の境界
- JWKS のモック化を通じた Backend API と Keycloak の通信の仕組み
- Authlib の例外型を区別することで得られる、失敗理由の特定能力

### 作成するファイル

- 新規: `docs/10_SetupJWTEdgeCaseTests.md`
- 参照: `docs/Reference/05_TokenClaimsAndValidation.md`（Phase 00 で作成済み）

### 主な扱う内容

- pytest と pytest-asyncio のセットアップ
- JWKS のモック化（テスト用の RSA 鍵ペア生成と fixture 化）
- テストケースの設計
  - 正常系: 正しい token が通る
  - 署名改ざん: payload を書き換えた token が弾かれる
  - `alg=none` 攻撃: アルゴリズムを `none` にした token が弾かれる
  - `kid` 不正: 存在しない `kid` を指定した token が弾かれる
  - `exp` 境界: 期限切れ直前 / 直後の挙動
  - `exp` 欠落: `exp` claim が存在しない token の扱い
  - `aud` 不一致: 別 audience の token が弾かれる
  - `iss` 不一致: 別 issuer の token が弾かれる
- Authlib の例外型の区別とログ出力への反映

### 想定する失敗例

- テスト用の鍵ペアを毎回生成すると遅い → fixture 化で解決
- Authlib の例外型を取り違えて、特定の失敗を捕捉できない
- JWKS モックの cache TTL を考慮しないテストで flaky になる

### 完了判定

- `docs/10_SetupJWTEdgeCaseTests.md` が作成されている
- `apps/demo_api/tests/test_auth.py` が作成され、上記の全テストケースが通る
- `pytest` 実行で全テストが green になる
- 既存の `auth.py` のロジックに変更を加えた場合、関連テストが失敗するように設計されている

---

## Phase 03: セキュリティ監査エージェント

### 学ぶ動機

Phase 02 までは「認証システムを作る側」の学習だった。この Phase では「監査する側」に回り、ログとイベントから不審なパターンを検出する LLM エージェントを実装する。

現職のセキュリティ運用経験（ログ収集と分析）と LLM エージェント実装を組み合わせた経験は、転職市場での希少価値が高い。

### 実装すると何が分かるか

- LLM エージェントの「ツール」設計とハルシネーション抑制の system prompt
- 決定的なコード（パターン検出）と LLM（要約・レポート生成）の役割分担
- Keycloak Admin REST API を使った運用自動化の入り口

### 作成するファイル

- 新規: `docs/11_SetupSecurityAuditAgent.md`
- 新規: `docs/Reference/07_AuditAndObservability.md`
- 新規: `agent/` ディレクトリ配下の実装ファイル

### 主な扱う内容（ハンズオン）

- `agent/` ディレクトリの作成と依存関係のセットアップ
- 4ツールの実装
  - `get_auth_logs`: FastAPI のアクセスログを取得
  - `analyze_pattern`: ブルートフォース・深夜アクセス・権限昇格試行を検出
  - `get_keycloak_events`: Keycloak Admin REST API からイベントを取得
  - `generate_report`: Markdown 形式の監査レポートを出力
- system prompt の設計（「推測で補完しない」「データに存在しない数値を出さない」ルール）
- エージェントの動作確認（疑似的な攻撃ログを投入して検出できるか）

### 主な扱う内容（Reference の前半部分）

- 観測対象の3層（認証ログ / Keycloak イベント / OTel トレース）
- ログとイベントの違い（アプリログ / Admin Event / User Event）
- LLM エージェントによる分析と決定的コードの役割分担

### 想定する失敗例

- 推測でログを補完してしまうハルシネーション → system prompt で抑制
- Admin API のトークン取得失敗 → service account の権限不足
- イベント検索クエリの誤り → Keycloak のイベント種別の理解不足

### 完了判定

- `docs/11_SetupSecurityAuditAgent.md` が作成されている
- `docs/Reference/07_AuditAndObservability.md` が作成されている（Phase 04 で更新される前提）
- `agent/` 配下に 4 ツールが実装されている
- 疑似ログを投入して、ブルートフォースなどのパターンが検出される
- Markdown レポートが生成される

---

## Phase 04: OpenTelemetry による認証フロー可視化

### 学ぶ動機

これまで失敗の切り分けは人力でログを横断的に追うしかなかった。マイクロサービス環境では分散トレーシングが必須になる。認証フローは「どの段階で落ちたか」を可視化したいケースが多く、OTel と相性が良い。

「観測性 vs プライバシー」のトレードオフを設計する経験を積む。

### 実装すると何が分かるか

- スパン属性の設計（何を記録し、何を記録すべきでないか）
- redaction processor による PII フィルタの設計
- context propagation の仕組みと、ミスったときの挙動

### 作成するファイル

- 新規: `docs/12_SetupOTelInstrumentation.md`
- 更新: `docs/Reference/07_AuditAndObservability.md`（Phase 03 で作成したものに、OTel 関連の章を追加）

### 主な扱う内容（ハンズオン）

- `opentelemetry-instrumentation-fastapi` の導入（BFF と Backend API 両方）
- カスタムスパン属性の設定
  - `auth.user.id`（`sub` claim）
  - `auth.result`（success / failure）
  - `auth.failure.reason`（expired / invalid_sig / aud_mismatch など）
- OTel Collector のセットアップ（Docker Compose に追加）
- redaction processor の設定で PII（`email`、`sub` の一部など）をマスク
- Jaeger または Tempo での可視化

### 主な扱う内容（Reference 追加部分）

- 観測性とプライバシーのトレードオフ
- スパン属性の設計指針（何を記録するか、何をマスクするか）
- context propagation の仕組み

### 想定する失敗例

- PII（`email` や `sub`）がスパン属性に漏れる
- redaction processor の設定ミスで本来マスクすべき値が出力される
- context propagation 漏れでトレースが繋がらない（BFF と Backend API が別々のトレースになる）

### 完了判定

- `docs/12_SetupOTelInstrumentation.md` が作成されている
- `docs/Reference/07_AuditAndObservability.md` に OTel 関連の章が追加されている
- OTel Collector が起動し、BFF と Backend API のトレースが連携される
- Jaeger / Tempo UI で 1 つのリクエストが BFF → Backend API として 1 本のトレースで見える
- redaction が効いて、PII がスパン属性に出力されないことを確認できる

---

## Phase 05: MCP サーバーの追加

### 学ぶ動機

MCP（Model Context Protocol）は AI エージェントと外部システムを接続するプロトコル。OAuth 2.1 と統合される設計になっており、`aud` 検証が中核的な防御策となる。

「OIDC 実装経験 × AI エージェント × 最新プロトコル」の三点セットは、転職市場での希少価値が高い。

### 実装すると何が分かるか

- `aud` 検証の重要性（confused deputy 問題の防御策として機能する）
- OAuth 2.1 と PKCE の必須性
- 複数 resource server 構成（同じ Keycloak から異なる `aud` の token を発行）

### 作成するファイル

- 新規: `docs/13_SetupMCPServer.md`
- 新規: `docs/Reference/08_MCPAuthorizationFlow.md`
- 新規: `apps/demo_mcp/` 配下の実装ファイル

### 主な扱う内容（ハンズオン）

- `apps/demo_mcp/` の新規作成（FastAPI ベース）
- echo ツール 1 本の実装
- Keycloak に `demo-mcp` client を追加
- Audience Mapper で `aud: demo-mcp` を付与
- MCP クライアントからの接続確認
- `aud` 検証が機能していることを確認

### 主な扱う内容（Reference）

- MCP プロトコルの概要
- MCP × OAuth 2.1 の認可フロー（Discovery → DCR → Authorization Code + PKCE）
- Resource Indicators (RFC 8707) と `aud` 固定
- Confused Deputy 問題の攻撃シナリオと防御策

### 想定する失敗例

- `aud` が `demo-api` のまま → MCP サーバー側で `401`
- PKCE の `code_verifier` 不一致
- `redirect_uri` 不一致

### 完了判定

- `docs/13_SetupMCPServer.md` が作成されている
- `docs/Reference/08_MCPAuthorizationFlow.md` が作成されている
- `apps/demo_mcp/` が起動し、`http://localhost:8002` でアクセスできる
- Keycloak に `demo-mcp` client が登録され、`aud: demo-mcp` の token が発行される
- 別の client（`demo-bff`）の token で MCP サーバーにアクセスすると `401` になる

---

## Phase 06: Next.js SPA + PKCE 構成

### 学ぶ動機

これまで BFF 構成（confidential client）しか触っていなかった。SPA + PKCE（public client）の構成も実務では非常に多い。

「`client_secret` を持てない世界」での認証を体験し、トークン保管場所のトレードオフを実装で理解する。

### 実装すると何が分かるか

- public client が secret を持てない理由と PKCE の必要性
- トークン保管場所のトレードオフ（localStorage / Cookie / in-memory）
- BFF 構成と SPA 構成の対比

### 作成するファイル

- 新規: `docs/14_SetupNextJsSPAWithPKCE.md`
- 新規: `docs/Reference/09_PublicClientAndPKCE.md`
- 新規: `apps/demo_web_spa/` 配下の実装ファイル

### 主な扱う内容（ハンズオン）

- `apps/demo_web_spa/` の新規作成（Next.js）
- Keycloak に SPA 用の public client を追加（`demo-web-spa`）
- PKCE 実装（`code_verifier` と `code_challenge` の生成）
- ブラウザでのトークン保管（in-memory）
- Backend API への直接アクセス（BFF を経由しない）
- BFF 構成との挙動比較

### 主な扱う内容（Reference の前半部分）

- public client と confidential client の違い
- PKCE の仕組み（`code_verifier` と `code_challenge` の関係）
- トークン保管場所の選択肢とトレードオフ

### 想定する失敗例

- `code_challenge_method` の不一致
- localStorage に token を置いた場合の XSS リスク
- CORS 設定漏れで Backend API にアクセスできない

### 完了判定

- `docs/14_SetupNextJsSPAWithPKCE.md` が作成されている
- `docs/Reference/09_PublicClientAndPKCE.md` が作成されている（Phase 07 で更新される前提）
- `apps/demo_web_spa/` が起動し、`http://localhost:3000` でアクセスできる
- Keycloak に `demo-web-spa` public client が登録されている
- ブラウザから PKCE フローでログインでき、Backend API を呼び出せる
- BFF 構成と SPA 構成の挙動の違いを Reference で説明できる

---

## Phase 07: Refresh Token と Back-channel Logout

### 学ぶ動機

これまで access token が切れたあとの挙動は触っていなかった。実務では「再ログイン地獄を避けつつセキュリティを保つ」のが大きな課題。

back-channel logout は SSO 環境で必須の機能で、「あるアプリでログアウトしたら他のアプリでも自動でログアウト」を実現する。

### 実装すると何が分かるか

- refresh token の保管責任（SPA では localStorage に置けないので BFF が必要）
- 非同期セキュリティイベントの設計（back-channel logout は HTTP 通知）
- logout token の検証（`events` claim を含む JWT 検証）

### 作成するファイル

- 新規: `docs/15_SetupRefreshAndLogout.md`
- 更新: `docs/Reference/09_PublicClientAndPKCE.md`（Phase 06 で作成したものに、refresh / logout 関連の章を追加）

### 主な扱う内容（ハンズオン）

- refresh token grant の実装（BFF 側）
- BFF session 内での refresh token 保管
- access token 期限切れ検知時の自動 refresh
- back-channel logout endpoint の実装
- logout token の検証（`iss` / `aud` / `events` claim）
- Keycloak の Back-Channel Logout URL 設定

### 主な扱う内容（Reference 追加部分）

- Refresh token のライフサイクルと保管責任
- Back-channel logout の動作と RP-initiated との対比
- logout token の検証観点

### 想定する失敗例

- refresh token を localStorage に置いた場合のリスク
- logout token の `events` claim 検証漏れ
- session 削除タイミングの race condition

### 完了判定

- `docs/15_SetupRefreshAndLogout.md` が作成されている
- `docs/Reference/09_PublicClientAndPKCE.md` に refresh / logout 関連の章が追加されている
- access token 期限切れ後に、自動で refresh されてアクセスが継続する
- Keycloak の管理コンソールから user の session を terminate すると、back-channel 経由で BFF の session が即座に無効化される
- logout token の改ざんを試すと、検証で弾かれることを確認できる

---

## 各 Phase 完了後にやること

各 Phase 完了時には、以下も併せて更新する。

- `docs/Reference/00_Glossary.md`: 新しく登場した用語を追加（例: `Hardcoded Claim Mapper`, `Resource Indicator`, `code_verifier`, `back-channel logout` など）
- `docs/Reference/01_LocalStartup.md`: 新しく追加したアプリの起動方法を記載（Phase 03, 04, 05, 06, 07 で更新）
- このファイル（`ROADMAP.md`）のステータス: 🔲 → ✅ に変更

---

## 進め方の指示テンプレート（Claude Code 用）

Claude Code に依頼するときは、以下のテンプレートを使う。

```
ROADMAP.md の Phase XX を実装してください。
ROADMAP.md の該当 Phase に記載されている「作成するファイル」「主な扱う内容」「想定する失敗例」「完了判定」に従って、必要なファイルを作成してください。

既存の docs/ の文体（既存の docs/05〜08 を参照）と Reference の文体（既存の Reference/02, 04 を参照）に揃えてください。

実装後、完了判定をすべて満たしているか self-check してください。
```

---

## 関連ドキュメント

- 既存の docs/ 全体
- 既存の docs/Reference/ 全体
- 既存の docs/_TEMPLATE.md（新規 docs の雛形）
