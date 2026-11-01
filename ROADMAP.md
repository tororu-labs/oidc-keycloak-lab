# oidc-keycloak-lab ROADMAP

> 更新日: 2026-11-01
>
> 目的: OIDC / BFF の学習基盤を完成させるため、完了済みの土台、現在の作業、将来候補を分けて管理する。

## 運用方針

- このリポジトリをコードと公開ドキュメントの唯一の編集元とする。
- `Completed Foundations` は実装・文書化済みの学習成果として維持する。
- `Active Roadmap` だけを現在の実行対象とし、原則としてPhase番号順に進める。
- `Backlog` はActive完了後に優先度と仕様を再評価する。
- `Parked` は再開条件を満たすまで着手しない。
- 調査途中のメモや秘密情報はコミットせず、再利用する内容だけを `docs/` へ整理する。

## 現在地

Keycloak、BFF、Backend API、SPAの基本構成に加え、token検証、refresh / logout、OpenTelemetryによる分散トレースまで実装済みです。

現在は機能追加を広げず、公開品質とOIDC / BFFのセキュリティ境界を整えることを優先します。

| 区分 | 状態 | 内容 |
|---|---|---|
| Completed Foundations | 完了 | `docs/01`〜`docs/13` の学習基盤 |
| Active Roadmap | 進行対象 | 公開品質とOIDC / BFFの堅牢化 |
| Backlog | 保留 | 認証監視、再現性、M2M、AI連携 |
| Parked | 停止 | 長寿命接続の認証 |

## Completed Foundations

既存のSetupと実装は作り直さず、今後のPhaseのベースラインとして扱います。

| Setup | 主な成果 |
|---|---|
| `docs/01`〜`docs/06` | GitHub、Python、Keycloak、FastAPI BFF / Backend APIの基本構成 |
| `docs/07`〜`docs/08` | Access Tokenの署名、`iss`、`aud`、`exp`検証と失敗系 |
| `docs/09` | Client ScopeとMapper |
| `docs/10` | JWT edge case tests |
| `docs/11` | Next.js SPA + Authorization Code Flow + PKCE |
| `docs/12` | BFFのRefresh Token、RP-Initiated Logout、Back-Channel Logout |
| `docs/13` | OpenTelemetryによる分散トレース、trace context伝搬、PII redaction、Jaeger |

OTelのtraceは完成済みの横断基盤です。認証イベント、metrics、ダッシュボード、アラートを含む監視全体は別のBacklogテーマとして扱います。

## Active Roadmap

| Phase | 内容 | 状態 | 作成・更新対象 |
|---|---|---|---|
| Phase 01 | Public Readiness | 進行中 | README、LICENSE、公開対象、リポジトリ運用の整理 |
| Phase 02 | Quality Baseline | 部分完了 | route test、CIの完了確認 |
| Phase 03 | OIDC State / Nonce / ID Token | 未着手 | `docs/14_SetupOIDCStateNonceAndIDToken.md` |
| Phase 04 | Session / Token Lifetime | 未着手 | `docs/15_SetupSessionAndTokenLifetime.md` |
| Phase 05 | BFF Cookie Security | 未着手 | `docs/16_SetupBFFCookieSecurity.md` |
| Phase 06 | Client Role Design | 未着手 | `docs/17_SetupClientRoleDesign.md` |

### Phase 01: Public Readiness

**目的:**

リポジトリの狙い、実装済み範囲、制約が第三者に伝わり、秘密情報を含めず安全に公開・継続開発できる状態にする。

**完了済み:**

- READMEにArchitecture、実装済み機能、Security Focus、Quick Startを記載した。
- production readyではないことをREADMEに明記した。
- MIT `LICENSE` を追加した。
- BFF、Backend API、SPAの設定例を用意した。
- ローカル絶対パスを公開ドキュメントから除去した。
- `.env` とローカル作業ファイルがGit管理外であることを確認した。
- このリポジトリを唯一の編集元とする運用へ変更した。

**残作業:**

- 変更全体のlint、type check、testを通す。
- READMEとdocsのリンク、記述、起動手順を最終確認する。
- GitHubリモートを設定し、PRで変更を取り込む。
- 旧リポジトリをメモ専用またはアーカイブとして整理する。

**完了判定:**

- secretやローカル絶対パスが追跡・記載されていない。
- READMEの説明と実装が一致している。
- CIとローカル検証が成功する。
- GitHub上でこのリポジトリが今後の編集元として運用できる。

### Phase 02: Quality Baseline

**目的:**

静的解析と基本テストによって、認証実装の変更を安全に検出できる状態にする。

**完了済み:**

- BFF / Backend APIのCIでRuff、mypy、pytestを実行する。
- SPAのCIで依存監査と本番ビルドを実行する。
- JWT検証の正常系・異常系テストが存在する。
- BFFの認証処理に対する単体テストが存在する。

**残作業:**

- BFF / Backend APIのimport testを追加する。
- 未ログイン時のredirectなど、基本route testを追加する。
- GitHubのbranch protectionで必須checkを設定する。

**完了判定:**

- lint、format、type check、testがCIで自動実行される。
- 最低限の起動・route動作を自動テストできる。
- CI失敗時にmainへ取り込めない運用になっている。

### Phase 03: OIDC State / Nonce / ID Token

**目的:**

Authorization Code FlowでBFFが検証すべき値と、利用ライブラリが担う範囲を実装と失敗ケースで確認する。

**主な内容:**

- `state` の生成、session保存、callback時の照合を確認する。
- `nonce` とID Tokenの関係を確認する。
- ID Tokenの署名、`iss`、`aud`、`exp`、`nonce`検証を整理する。
- state不一致、nonce不一致、ID Token不正を再現する。
- ライブラリの自動検証範囲とアプリ責務を文書化する。

**完了判定:**

- 正常系と主要な不一致ケースをテストできる。
- ブラウザ表示とログから失敗段階を判別できる。
- 検証責務をSetupとReferenceで説明できる。

### Phase 04: Session / Token Lifetime

**目的:**

BFF session、Access Token、Refresh Token、Keycloak sessionの寿命と更新責務を整理する。

**主な内容:**

- 各lifetimeと設定元を比較する。
- Access Token期限切れ前後のrefresh動作を確認する。
- refresh失敗時のsession破棄と再ログイン導線を確認する。
- role変更後にsession内の表示情報が古くなるケースを整理する。
- clock skewと更新バッファの意味を整理する。

**完了判定:**

- 各lifetimeの設定元と失効時の動作を説明できる。
- refresh成功・失敗・session期限切れを再現できる。
- ブラウザ表示、ログ、実装の失敗段階が一致する。

### Phase 05: BFF Cookie Security

**目的:**

localhost用Cookie設定と本番設定を分け、Cookie sessionを使うBFFに必要なCSRF防御を整理する。

**主な内容:**

- `HttpOnly`、`Secure`、`SameSite`、Cookie名と有効期限を確認する。
- localとproductionのCookie設定を環境変数で分離する。
- 状態変更endpoint、特にlogoutのCSRF対策を実装する。
- Origin / Referer検証とCSRF tokenの役割を整理する。

**完了判定:**

- localとproductionのCookie属性を切り替えられる。
- logoutに対する正規リクエストとCSRFリクエストをテストできる。
- Cookie属性とCSRF防御の関係を説明できる。

### Phase 06: Client Role Design

**目的:**

Realm RoleとClient Roleのtoken上の違いを確認し、サービス固有権限の設計基準を整理する。

**主な内容:**

- `realm_access.roles` と `resource_access.<client_id>.roles` を比較する。
- Keycloakで `demo-api` のClient Roleを作成・割り当てする。
- Backend APIが参照するroleの範囲を明示する。
- 全体共通権限とサービス固有権限の使い分けを整理する。

**完了判定:**

- token上でRealm RoleとClient Roleの違いを確認できる。
- Backend APIの認可対象となるroleをテストで固定できる。
- roleの選択基準がReferenceに整理されている。

## Backlog

Active Roadmapの完了後に必要性と実装順を再評価します。Activeへ昇格するまでPhase番号やSetup番号は予約しません。

| テーマ | 学習目的 |
|---|---|
| Authentication Monitoring Baseline | Keycloak Login / Admin Event、アプリ認証ログ、OTel Metrics、ダッシュボード、検知ルール、アラートを整備する |
| Keycloak Configuration as Code | realm / client / mapper設定の再現性と復旧 |
| Client Credentials / M2M | ユーザーを介さないservice accountの認証・認可 |
| MCP Authorization | resource serverごとの `aud` とOAuth連携 |
| Security Audit Agent | 認証ログを入力とした調査支援とツール設計 |

監視関連は、完成済みのOTel traceを土台に `Authentication Monitoring Baseline` を整備し、その後に `Security Audit Agent` を検討します。

## Parked

| テーマ | 停止理由 | 再開条件 |
|---|---|---|
| SSE認証 | 長寿命接続へ対象が広がる | Active Roadmap完了後、logout通知の必要性を再評価する |
| WebSocket認証 | handshakeとmessage-level authorizationが別テーマになる | 長寿命接続の学習目的を再定義する |

## 更新ルール

Active Phaseの完了時は、次を同じ変更単位で更新します。

- Phaseの状態と完了判定
- 作成したSetupと関連Referenceへのリンク
- `docs/Reference/00_Glossary.md` の必要な用語
- `docs/Reference/01_LocalStartup.md` の起動方法
- READMEの実装済み機能と現在の焦点

新しいテーマは直接Activeへ追加せず、まずBacklogに置きます。Activeの完了または優先順位変更が明確になった時点で、Phase番号とSetup番号を割り当てます。

## 関連ドキュメント

- [README.md](README.md)
- [docs/](docs/README.md)
- [Setup template](docs/_TEMPLATE.md)
