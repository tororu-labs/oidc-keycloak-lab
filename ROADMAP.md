# iam-lab-study ROADMAP

> 作成日: 2026-05-17（v2 改訂日: 2026-06-23）
> 目的: docs/ と docs/Reference/ の追加計画を、フェーズ単位で着手・完了判定できる形に整理する
> 使い方: Claude Code に「ROADMAP の Phase XX を実装してほしい」と指示する。1フェーズ単位で進め、完了判定を満たしてから次へ移る。

---

## このロードマップの読み方

- 各 Phase は **1つのハンズオン docs と 0〜1つの座学 Reference** で構成される
- Phase は **依存関係順** に並んでいる。原則として前の Phase の完了判定を満たしてから次へ進む
- ポートフォリオ優先度（🔴/🟡/🟢）を参考に、優先度の高い Phase を先に進める
- 各 Phase には以下を記載する
  - **学ぶ動機**: なぜこの Phase が必要か
  - **実装すると何が分かるか**: 実装を通じて獲得する理解
  - **作成するファイル**: 新規作成または更新するファイル
  - **主な扱う内容**: 中で扱うトピックの一覧
  - **想定する失敗例**: 学習価値の高い失敗ケース
  - **完了判定**: この Phase を「完了」と見なす条件

---

## 現在地（2026-06-23 時点）

実ファイルの存在確認に基づく完了状態。

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 00 | Reference 切り出し | ✅ 完了 |
| Phase 01 | Public Readiness | ⚠️ 部分完了 |
| Phase 02 | Quality Baseline（pytest + CI） | ⚠️ 部分完了 |
| Phase 03 | JWT Edge Case Tests | ✅ 完了 |
| Phase 04 | Client Scope & Mapper | ✅ 完了 |
| Phase 05 | Client Role vs Realm Role | 🔲 未着手 |
| Phase 06 | Session / Token Lifetime | 🔲 未着手 |
| Phase 07 | BFF Cookie Security | 🔲 未着手 |
| Phase 08 | Refresh Token & Back-channel Logout | ✅ 完了 |
| Phase 09 | Keycloak Config as Code | 🔲 未着手 |
| Phase 10 | SSE 認証 | 🔲 未着手 |
| Phase 11 | WebSocket 認証 | 🔲 未着手 |
| Phase 12 | OTel | ✅ 完了 |
| Phase 13 | Security Audit Agent | 🔲 未着手 |
| Phase 14 | SPA + PKCE（Next.js） | ✅ 完了 |
| Phase 15 | MCP | 🔲 未着手 |
| Phase 16 | Client Credentials（M2M） | 🔲 未着手 |

**⚠️ 部分完了の内訳:**
- Phase 01: `.github/workflows/ci.yml` はあり。`LICENSE`・`.env.example` はなし。
- Phase 02: `apps/demo_api/tests/test_auth.py` と `ci.yml` はあり。lint 設定は未確認。

---

## Phase 一覧と優先度

| Phase | 内容 | ポートフォリオ優先度 | 状態 |
|-------|------|-----------------|------|
| Phase 00 | Reference 切り出し | — | ✅ 完了 |
| Phase 01 | Public Readiness | 🔴 高（公開の前提） | ⚠️ 部分完了 |
| Phase 02 | Quality Baseline | 🔴 高（最初に見られる） | ⚠️ 部分完了 |
| Phase 03 | JWT Edge Case Tests | 🔴 高（セキュリティ専門性） | ✅ 完了 |
| Phase 04 | Client Scope & Mapper | 🟡 中 | ✅ 完了 |
| Phase 05 | Client Role vs Realm Role | 🟡 中（IAM 設計の深さ） | 🔲 未着手 |
| Phase 06 | Session / Token Lifetime | 🟡 中 | 🔲 未着手 |
| Phase 07 | BFF Cookie Security | 🟡 中（Web セキュリティ基礎） | 🔲 未着手 |
| Phase 08 | Refresh Token & Back-channel Logout | 🟡 中 | ✅ 完了 |
| Phase 09 | Keycloak Config as Code | 🟢 低〜中（再現性） | 🔲 未着手 |
| Phase 10 | SSE 認証 | 🟢 低（応用） | 🔲 未着手 |
| Phase 11 | WebSocket 認証 | 🟢 低（応用） | 🔲 未着手 |
| Phase 12 | OTel | 🟡 中（観測性） | ✅ 完了 |
| Phase 13 | Security Audit Agent | 🔴 高（差別化） | 🔲 未着手 |
| Phase 14 | SPA + PKCE（Next.js） | 🟡 中（フルスタック） | ✅ 完了 |
| Phase 15 | MCP | 🔴 高（AI × 認証） | 🔲 未着手 |
| Phase 16 | Client Credentials（M2M） | 🟡 中（実務スキル） | 🔲 未着手 |

---

## 全体マップ

### docs/ と docs/Reference/ の対応関係

```
docs/                                  docs/Reference/
────────────────────────────────────────────────────────────────────
                                       00_Glossary.md          ← 全体共通
                                       01_LocalStartup.md      ← 全体共通

── 完了済み ──────────────────────────────────────────────────────
08_SetupAudienceValidation ──┐
09_SetupClientScopeAndMapper ┼──→ 05_TokenClaimsAndValidation  ← ✅ Phase 00, 03
10_SetupJWTEdgeCaseTests ────┘    06_ClientScopeAndMapperTypes ← ✅ Phase 04

11_SetupNextJsSPAWithPKCE ───┐
12_SetupRefreshAndLogout ────┴──→ 08_PublicClientAndPKCE       ← ✅ Phase 08, 14

13_SetupOTelInstrumentation ─────→ 09_Observability            ← ✅ Phase 12 完了

── 未着手 ────────────────────────────────────────────────────────
Phase 05 Client Role ────────────→ 06_ClientScopeAndMapperTypes（追記）

Phase 13 Security Audit Agent ──→ 10_AuditAgentDesign          ← 新規

Phase 15 MCP ────────────────────→ 11_MCPAuthorizationFlow     ← 新規

Phase 16 M2M 認証 ───────────────→ 12_MachineToMachineAuth     ← 新規
```

---

## 各 Phase の詳細

---

### Phase 00: 既存 docs/08 の座学を Reference に切り出す ✅ 完了

**作成済みファイル:** `docs/Reference/05_TokenClaimsAndValidation.md`

---

### Phase 01: Public Readiness ⚠️ 部分完了

**目的:** GitHub repository を public 化しても安全な状態に整える。

**残作業:**
- `LICENSE` を追加する
- `.env.example` を整備する（`apps/demo_api/.env.example`、`apps/demo_bff/.env.example` など）
- README を刷新する（Architecture / Features / Quick Start / Security Notes / Roadmap を含む）
- `notes/` と `scratch/` の公開可否を整理する
- ドキュメント内の絶対パスリンクを相対パスに修正する
- `infra/keycloak/.env` が git 追跡されていないか確認する（`git ls-files infra/keycloak/.env`）
- `apps/demo_api/auth.py` のコメントアウト旧コードを削除する
- production ready ではないことを README に明記する

**完了済み:**
- `.github/workflows/ci.yml` が存在する

**完了判定:**
- `LICENSE` が追加されている
- `.env.example` が各アプリに存在する
- README に Architecture / Quick Start / Security Notes が含まれている
- `git ls-files` で `.env` や secret ファイルが追跡されていないことを確認できる

---

### Phase 02: Quality Baseline ⚠️ 部分完了

**目的:** テスト・lint が自動で実行される品質基盤を作る。

**残作業:**
- ruff などの lint / format 設定を整備する
- CI で lint が実行されているか確認し、なければ追加する
- BFF / Backend API の import test を追加する（起動確認レベルの最低限テスト）
- 未ログイン時 redirect などの基本 route test を追加する

**完了済み:**
- `apps/demo_api/tests/test_auth.py` が存在する（JWT 検証テスト）
- `.github/workflows/ci.yml` が存在する

**完了判定:**
- `pytest` が CI で自動実行される
- lint / format が CI で自動実行される
- PR 時に CI が走り、失敗時にマージをブロックできる状態になっている

---

### Phase 03: JWT Edge Case Tests ✅ 完了

**作成済みファイル:** `docs/10_SetupJWTEdgeCaseTests.md`、`apps/demo_api/tests/test_auth.py`

**扱った内容:** 署名改ざん・`alg=none` 攻撃・`kid` 不正・`exp` 境界・`aud` 不一致・`iss` 不一致の異常系テスト

---

### Phase 04: Client Scope と Mapper の体系整理 ✅ 完了

**作成済みファイル:** `docs/09_SetupClientScopeAndMapper.md`、`docs/Reference/06_ClientScopeAndMapperTypes.md`

---

### Phase 05: Client Role vs Realm Role 🔲 未着手

**学ぶ動機:**
Phase 04 で Mapper の設定を学んだ後、「どの role を使うべきか」という設計判断が問われる。
`realm_access.roles` と `resource_access.<client_id>.roles` の違いを実装で確認し、設計観点として整理する。
`Reference/04_ClientAndTokenRoles.md` で「今後の拡張ポイント」として先送りされていた内容を回収する。

**実装すると何が分かるか:**
- `realm_access.roles` と `resource_access.<client_id>.roles` の token 上の位置の違い
- 「全 client 共通 → realm role」「サービス固有 → client role」という設計判断基準

**作成するファイル:**
- 新規: `docs/14_SetupClientRoleDesign.md`
- 更新: `docs/Reference/06_ClientScopeAndMapperTypes.md`（client role の節を追加）

**主な扱う内容:**
- Keycloak で `demo-api` の client role（`api-reader` / `api-writer`）を作成する
- alice / bob に client role を割り当てる
- Token Evaluate で `resource_access.demo-api.roles` に現れることを確認する
- realm role（`viewer` / `admin`）と client role の token 上の位置を並べて比較する
- 設計判断基準を Reference に整理する

**想定する失敗例:**
- client role を設定したのに token に現れない → mapper の設定漏れ
- `realm_access.roles` を見る実装のまま client role を設定しても Backend API の認可が変わらない

**完了判定:**
- `docs/14_SetupClientRoleDesign.md` が作成されている
- Token Evaluate で `resource_access.demo-api.roles` に client role が表示される
- `Reference/06` に realm role vs client role の設計判断の節が追加されている

---

### Phase 06: Session / Token Lifetime 🔲 未着手

**学ぶ動機:**
BFF session と Access Token の寿命の違いを整理し、現在の実装で起こり得る認可結果の食い違いを扱う。
role 変更後に session 内の古い role が残るケースなど、BFF 構成の便利さだけでなく落とし穴を理解する。

**実装すると何が分かるか:**
- BFF session TTL と Access Token `exp` の独立した管理
- role 変更後の session 内 role の問題と対処方針
- 再ログインさせる設計と refresh する設計のトレードオフ

**作成するファイル:**
- 新規: `docs/15_SetupSessionAndTokenLifetime.md`

**主な扱う内容:**
- BFF session TTL の設定と確認
- Access Token `exp` との対比
- BFF の `/admin` と Backend API の `/api/admin-data` の認可タイミングの違い
- role 変更後の挙動確認と対処方針
- token 期限切れ時の UX

**完了判定:**
- `docs/15_SetupSessionAndTokenLifetime.md` が作成されている
- session TTL と Access Token `exp` の違いをブラウザと Keycloak コンソールで確認できる
- role 変更後の動作が期待通りになっている

---

### Phase 07: BFF Cookie Security 🔲 未着手

**学ぶ動機:**
Cookie session を使う BFF 構成で必要になる Web security の基礎を整理する。
CSRF・SameSite・HttpOnly・Secure の設定が揃っていないと、認証が正しく動いていても攻撃経路が残る。

**実装すると何が分かるか:**
- Cookie session における主要な防御属性の意味と設定方法
- CSRF 対策の実装パターン
- local 環境と production 環境での設定差分

**作成するファイル:**
- 新規: `docs/16_SetupBFFCookieSecurity.md`

**主な扱う内容:**
- CSRF 対策の実装（logout endpoint 含む）
- `SameSite` / `HttpOnly` / `Secure` の設定確認と意味
- セッション Cookie 名のデフォルト変更
- local development と production の設定差分の整理

**完了判定:**
- `docs/16_SetupBFFCookieSecurity.md` が作成されている
- CSRF トークンが logout endpoint で検証される
- Cookie が `HttpOnly`・`SameSite=Lax`（または Strict）で設定されている

---

### Phase 08: Refresh Token と Back-channel Logout ✅ 完了

**作成済みファイル:** `docs/12_SetupRefreshAndLogout.md`、`docs/Reference/08_PublicClientAndPKCE.md`（refresh / logout 関連章を追加済み）

---

### Phase 09: Keycloak Configuration as Code 🔲 未着手

**学ぶ動機:**
GUI 手順だけに依存した設定は再現性がない。他の人が手元で再現でき、設定を壊したときに復旧できるリポジトリにする。

**実装すると何が分かるか:**
- `kcadm.sh` を使った Keycloak 設定の自動化
- realm export / import による設定の保存と復元

**作成するファイル:**
- 新規: `docs/17_SetupKeycloakAsCode.md`
- 新規: `infra/keycloak/setup.sh`（bootstrap スクリプト）

**主な扱う内容:**
- `kcadm.sh` による realm / user / role / client / mapper の作成
- realm export / import
- local bootstrap script の整備
- 設定を壊したときの復旧手順

**完了判定:**
- `docs/17_SetupKeycloakAsCode.md` が作成されている
- `infra/keycloak/setup.sh` を実行すると、Keycloak の初期設定が再現できる
- スクリプトを実行した状態で既存のハンズオン手順が動作する

---

### Phase 10: SSE 認証 🔲 未着手

**学ぶ動機:**
SSE はブラウザからサーバーへの長寿命な一方向接続。接続中に token が切れたり session が無効化された場合の認証状態管理は、通常の HTTP request とは異なる問題を持つ。

**実装すると何が分かるか:**
- Cookie session 付きの SSE 接続の実装
- 接続中の session 無効化に対する応答設計

**作成するファイル:**
- 新規: `docs/18_SetupSSEAuth.md`

**主な扱う内容:**
- BFF に `/events` SSE endpoint を追加
- Cookie session 付きの SSE 接続
- session expired 通知・logout 通知の実装
- back-channel logout と連動したブラウザへのリアルタイム通知
- 接続中に session が無効化された場合の扱い

**完了判定:**
- `docs/18_SetupSSEAuth.md` が作成されている
- BFF logout 時に SSE 経由でブラウザへ通知が届く
- session が無効化されたとき、SSE 接続が適切に終了する

---

### Phase 11: WebSocket 認証 🔲 未着手

**学ぶ動機:**
WebSocket は双方向の長寿命接続。handshake 時の認証と、接続中の role 変更・token 切れの扱いは SSE とは異なる論点を持つ。

**実装すると何が分かるか:**
- WebSocket handshake 時の認証方式の選択肢
- 接続中の token expiry / role change への対応方針

**作成するファイル:**
- 新規: `docs/19_SetupWebSocketAuth.md`

**主な扱う内容:**
- WebSocket handshake 時の認証（Cookie session vs Bearer token）
- 接続中の token expiry への対応
- logout / role change 時の切断処理
- origin check
- message-level authorization
- SSE との違いの整理

**完了判定:**
- `docs/19_SetupWebSocketAuth.md` が作成されている
- 未認証の接続がハンドシェイク時に拒否される
- 接続中に session が無効化されると切断される

---

### Phase 12: OpenTelemetry による認証フロー可視化 ✅ 完了

**作成済みファイル:** `docs/13_SetupOTelInstrumentation.md`、`docs/Reference/09_Observability.md`

**扱った内容:** BFF / Backend API への OTel 計装・カスタムスパン属性（`auth.user.id`・`auth.result`・`auth.failure.reason`・`auth.user.email`）・redaction processor による PII マスク・Jaeger での可視化

---

### Phase 13: セキュリティ監査エージェント 🔲 未着手

**学ぶ動機:**
Phase 12 で OTel による可視化を済ませているため、エージェントは構造化された認証ログを入力にできる。
現職のセキュリティ運用経験（ログ収集と分析）と LLM エージェント実装を組み合わせることで、転職市場での差別化ポイントになる。

実装は **Step 1（パイプライン固定）→ Step 2（LLM が調査判断）** の 2 段階で積み上げる。先にツールが正しく動くことを確認してから、エージェントループに切り替えることで、デバッグの切り分けがしやすくなる。

**実装すると何が分かるか:**
- ツール設計の柔軟性の重要性（Step 2 で作り直さないためのインターフェース設計）
- LLM に何を判断させ、何をコードで制御するかの境界
- エージェントループの制御（max_iterations、終了条件）
- ハルシネーション抑制の system prompt 設計
- Keycloak Admin REST API を使った運用自動化の入り口

**作成するファイル:**
- 新規: `docs/20_SetupSecurityAuditAgent.md`
- 新規: `docs/Reference/10_AuditAgentDesign.md`
- 新規: `apps/demo_agent/` 配下の実装ファイル

**主な扱う内容:**

Step 1（パイプライン固定でレポートを出す）:
- 5 ツールの実装（最初から柔軟なインターフェースで設計する）
  - `search_logs(stage=None, user=None, reason=None, limit=50)`: FastAPI ログを条件で絞り込んで取得
  - `get_user_events(user_id, event_type=None)`: 対象ユーザーの Keycloak イベントを取得
  - `get_ip_activity(ip_address)`: 対象 IP の全アクティビティを横断取得
  - `check_keycloak_admin_events(time_range=None)`: 権限昇格・設定変更イベントを取得
  - `generate_report(findings)`: Markdown 形式の監査レポートを出力
- 固定順でツールを呼び出してレポートが生成されることを確認する

Step 2（LLM に調査判断を委ねる）:
- エージェントループの実装（LLM がツールを選んで繰り返し呼び出す）
- system prompt の設計（「推測で補完しない」「疑わしいパターンを見つけたら IP とユーザー両方を調べる」）
- ループ制御（max_iterations、終了条件）

**LLM プロバイダー:** Anthropic API（Claude）を使用する。

**想定する失敗例:**
- Step 1 でツールのインターフェースを固定（引数なし）で作ると、Step 2 で作り直しになる
- 推測でログを補完してしまうハルシネーション → system prompt で抑制
- Admin API のトークン取得失敗 → service account の権限不足
- LLM に決定的処理（例: 数値しきい値判定）を任せて精度が落ちる
- ループが止まらない → max_iterations と終了条件の設計漏れ

**完了判定:**

Step 1:
- `apps/demo_agent/` 配下に 5 ツールが実装されている
- 固定順でツールを呼び出してレポートが生成される
- レポートに含まれる数値・固有名詞が入力データに実在する（ハルシネーションなし）

Step 2:
- `docs/20_SetupSecurityAuditAgent.md` が作成されている
- `docs/Reference/10_AuditAgentDesign.md` が作成されている
- エージェントループが実装されている
- 疑似ログを投入して、LLM がブルートフォースなどのパターンを検出し、対象ユーザー・IP を自動的に深掘りする
- 入力データの内容によって LLM のツール呼び出し順が変わることを確認できる
- ループが max_iterations を超えずに終了する

---

### Phase 14: Next.js SPA + PKCE 構成 ✅ 完了

**作成済みファイル:** `docs/11_SetupNextJsSPAWithPKCE.md`、`docs/Reference/08_PublicClientAndPKCE.md`、`apps/demo_web_spa/`

---

### Phase 15: MCP サーバーの追加 🔲 未着手

**学ぶ動機:**
MCP（Model Context Protocol）は OAuth 2.1 と統合される設計になっており、`aud` 検証が中核的な防御策になる。
「OIDC 実装経験 × AI エージェント × 最新プロトコル」の三点セットは転職市場での希少価値が高い。

**実装すると何が分かるか:**
- `aud` 検証の重要性（confused deputy 問題の防御策として機能する）
- OAuth 2.1 と PKCE の必須性
- 複数 resource server 構成（同じ Keycloak から異なる `aud` の token を発行）

**作成するファイル:**
- 新規: `docs/21_SetupMCPServer.md`
- 新規: `docs/Reference/11_MCPAuthorizationFlow.md`
- 新規: `apps/demo_mcp/` 配下の実装ファイル

**主な扱う内容:**
- `apps/demo_mcp/` の新規作成（FastAPI ベース）
- echo ツール 1 本の実装
- Keycloak に `demo-mcp` client を追加
- Audience Mapper で `aud: demo-mcp` を付与
- MCP クライアントからの接続確認と `aud` 検証の動作確認
- Confused Deputy 問題の攻撃シナリオと防御策を Reference に整理

**完了判定:**
- `docs/21_SetupMCPServer.md` が作成されている
- `docs/Reference/11_MCPAuthorizationFlow.md` が作成されている
- `apps/demo_mcp/` が起動し、`http://localhost:8002` でアクセスできる
- `demo-bff` の token で MCP サーバーにアクセスすると `401` になる

---

### Phase 16: Client Credentials Grant（M2M 認証） 🔲 未着手

**学ぶ動機:**
これまでのフロー全体が「ユーザーがログインする」前提。実務ではバックグラウンドジョブやサービス間 API 呼び出しのように、ユーザーが介在しない Machine-to-Machine 認証が頻繁に登場する。
最後に Authorization Code Flow との対比を置くことで、「どちらを使うべきか」の設計判断まで説明できる状態になる。

**実装すると何が分かるか:**
- Client Credentials grant のフローと token の中身（`sub` が service account になる）
- service account の役割と権限設計
- Authorization Code Flow との設計対比

**作成するファイル:**
- 新規: `docs/22_SetupClientCredentials.md`
- 新規: `docs/Reference/12_MachineToMachineAuth.md`
- 新規: `apps/demo_job/`（簡単なスクリプト）

**主な扱う内容:**
- Keycloak で `demo-job` client を作成し、service account を有効化する
- `client_credentials` grant で token を取得する（httpx で token endpoint を直接叩く）
- 取得した token で Backend API を呼び出す
- token の中身を確認する（`sub` が service account の UUID になることを確認）
- Authorization Code Flow との対比を Reference に整理する

**想定する失敗例:**
- service account を有効化していないと `unauthorized_client` が返る
- `aud` 設定を忘れて `demo-job` 向けの token が Backend API の検証を通過してしまう

**完了判定:**
- `docs/22_SetupClientCredentials.md` が作成されている
- `apps/demo_job/` のスクリプトが token を取得して Backend API を呼び出せる
- token の `sub` が service account であることを確認できる
- Reference で Authorization Code Flow との設計対比が説明されている

---

## 転職活動（6〜7月）との対応

現在地: **OTel 計装完了 / Phase 13（Security Audit Agent）着手前**

```
                     現在 ─────── 6月下旬 ────── 7月（活動開始）
                       │             │
✅ IAM 基盤完成        Phase 13     Phase 15
（BFF + SPA + OTel）  （Audit Agent）（MCP）

                       ↓
                Phase 01/02 補完（Public Readiness + Quality Baseline）
                転職活動と並行
```

- **現時点**: OIDC/OAuth2 実装 + OTel 計装済み。BFF / SPA 両構成 + token ライフサイクル完結
- **Phase 13 完了時点**: 認証基盤 + 観測性 + LLM エージェント設計。DevSecOps 寄りのアピールが可能になる
- **Phase 15 完了時点**: IAM × AI × 最新プロトコル（MCP）の三点セット
- **Phase 01/02**: 転職活動と並行して Public Readiness / Quality Baseline を補完する

---

## 各 Phase 完了後にやること

- `docs/Reference/00_Glossary.md`: 新しく登場した用語を追加
- `docs/Reference/01_LocalStartup.md`: 新しく追加したアプリの起動方法を記載
- `ROADMAP.md` のステータスを更新する

---

## 未解決の判断事項

| 判断事項 | 選択肢 | 現時点の暫定方針 |
|---|---|---|
| Phase 09（Keycloak Config as Code）の位置 | 含める / 先送り | 含めるが後半に置く |
| Phase 10・11（SSE / WebSocket）の必要性 | 含める / 先送り | 応用テーマとして含めるが低優先 |
| Phase 13（Audit Agent）の LLM プロバイダー | Anthropic API / OpenAI / その他 | Anthropic API（Claude）を使用する |

---

## 短期マイルストーン

### Milestone 1: Public Readiness（Phase 01 残作業）

LICENSE・`.env.example`・README 刷新・絶対パスリンク修正を完了させる。

### Milestone 2: Quality Baseline 補完（Phase 02 残作業）

lint / format 設定と基本 route test を追加して CI を完備させる。

### Milestone 3: IAM 深掘り（Phase 05〜08）

Client Role 設計・Session/Token Lifetime・Cookie Security（Refresh & Logout は完了済み）。

### Milestone 4: 応用拡張（Phase 09〜16）

Keycloak Config as Code・SSE・WebSocket・OTel・Audit Agent・MCP・M2M 認証。

---

## 進め方の指示テンプレート（Claude Code 用）

Claude Code に依頼するときは、以下のテンプレートを使う。

```
ROADMAP の Phase XX を実装してください。
該当 Phase に記載されている「作成するファイル」「主な扱う内容」「想定する失敗例」「完了判定」に従って、必要なファイルを作成してください。

既存の docs/ の文体（既存の docs/05〜08 を参照）と Reference の文体（既存の Reference/02, 04 を参照）に揃えてください。

実装後、完了判定をすべて満たしているか self-check してください。
```

---

## 関連ドキュメント

- `docs/` 全体
- `docs/Reference/` 全体
- `docs/_TEMPLATE.md`
