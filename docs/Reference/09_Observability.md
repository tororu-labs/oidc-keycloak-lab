# 09 Observability — 分散トレーシングと認証フローの可視化

## 目的

このドキュメントは、OpenTelemetry（OTel）を使った分散トレーシングの概念と、認証フローへの適用における設計指針を整理するものである。

ハンズオン手順は [13_SetupOTelInstrumentation.md](../13_SetupOTelInstrumentation.md) を参照する。

------

## 分散トレーシングの基本概念

### trace とは

1 つのリクエストが複数のサービスを横断したとき、その一連の処理を 1 つの単位として記録したもの。  
`trace_id`（128 bit）で識別する。

### span とは

trace を構成する個々の処理単位。  
HTTP リクエスト、関数呼び出し、外部 API 呼び出しなど、時間的に区切れる処理が 1 つのスパンに対応する。スパンには次の情報が含まれる。

| フィールド | 内容 |
|---|---|
| `trace_id` | どの trace に属するか |
| `span_id` | このスパン自身の識別子 |
| `parent_span_id` | 呼び出し元スパンの識別子 |
| 開始時刻・終了時刻 | 処理にかかった時間 |
| 属性（attributes） | key-value で付与する任意の情報 |
| ステータス | `OK` / `ERROR` |

### context propagation とは

あるサービスのスパンから別サービスのスパンに `trace_id` と `parent_span_id` を引き継ぐ仕組み。  
HTTP では `traceparent` ヘッダー（W3C Trace Context 仕様）として伝搬する。

BFF → Backend API のケースでは、BFF の httpx クライアントが `traceparent` ヘッダーを自動付与し、API 側の FastAPI が受信して同一 `trace_id` のスパンを生成する。これにより、BFF と API が別プロセスでも 1 本のトレースに繋がる。

------

## このラボの OTel 構成

~~~
アプリ                Collector                 Jaeger
─────────────────────────────────────────────────────
demo-bff (BFF)   ──→  OTel Collector  ──→  Jaeger
demo-api (API)   ──→  (redaction処理)       (可視化)
                       port 4318 HTTP
~~~

| コンポーネント | 役割 |
|---|---|
| `opentelemetry-instrumentation-fastapi` | FastAPI の各 route を自動的にスパンとして記録する |
| `opentelemetry-instrumentation-httpx` | BFF の httpx リクエストに `traceparent` を付与し、response のスパンを記録する |
| `OTel Collector` | アプリからトレースを受け取り、redaction 処理をしてから Jaeger に転送する |
| `Jaeger` | トレースを蓄積し、UI で可視化する |

------

## スパン属性の設計指針

### 何を記録するか

認証フローでは次の属性を付与する。

| 属性名 | 値の例 | 意味 |
|---|---|---|
| `auth.user.id` | UUID 形式の `sub` claim | ログインしたユーザーの識別子 |
| `auth.result` | `success` / `failure` | 認証が成功したか失敗したか |
| `auth.failure.reason` | `expired` / `invalid_sig` / `aud_mismatch` / `jose_error` | 失敗の原因 |

`sub` claim は UUID 形式のランダム値であり、email や username のような表示可能な個人情報ではないため、スパン属性として記録してよい。

### 何を記録すべきでないか

スパン属性にはトレースバックエンドが保存するため、次のような情報は記録しない。

| 記録すべきでない情報 | 理由 |
|---|---|
| `email` / `preferred_username` | 個人を特定できる情報（PII） |
| access token / refresh token の値 | 悪用されると他サービスへの不正アクセスに使われる |
| client secret / session secret | 秘密情報 |

------

## 観測性とプライバシーのトレードオフ

「何をスパン属性に入れるか」は観測性とプライバシーのトレードオフである。

- 観測性を高めるには、失敗理由・ユーザー識別子・処理時間など多くの情報をスパンに入れたい
- プライバシー保護の観点では、PII（個人情報）はスパンに入れるべきでない

このラボでは次の方針を採る。

- **記録する**: `sub`（UUID 形式）、`auth.result`、`auth.failure.reason`
- **記録しない**: `email`、`preferred_username`、token の値
- **Collector で防衛する**: 万が一 PII がスパン属性に入った場合でも、redaction processor でマスクする

------

## redaction processor とは

OTel Collector の contrib パッケージ（`otel/opentelemetry-collector-contrib`）が提供するプロセッサー。スパン属性の値に対して正規表現パターンマッチを行い、一致した値を `****` に置き換える。

このラボの設定:

~~~yaml
processors:
  redaction:
    allow_all_keys: true       # 属性キーの制限はしない
    blocked_values:
      # email アドレスパターンをマスクする
      - "[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}"
    summary: debug             # 開発環境専用。本番では削除する。
~~~

`summary: debug` を有効にすると、マスクされたキー名と件数が `redaction.masked.keys` / `redaction.masked.count` としてスパン属性に付加される。Jaeger UI の Tags で確認できる。本番環境では削除する。

------

## no-op 設計について

このラボでは `OTEL_EXPORTER_OTLP_ENDPOINT` が未設定の場合、`setup_telemetry()` が早期 return して何もしない。

メリット:

- OTel なしの既存の起動手順を壊さない
- Collector が停止していても、アプリの動作に影響しない
- `BatchSpanProcessor` は送信失敗を非同期でサイレントに処理するため、Collector の一時停止でアプリはクラッシュしない

### import の分割について

`auth.py` や `main.py` では `from opentelemetry import trace` をファイル先頭でインポートしている。一方 `telemetry.py` では OTel の主要パッケージ（`sdk`・`exporter`）を `if` ブロック内で遅延インポートしている。

この違いは意図的なものである。

- `opentelemetry-api`（`from opentelemetry import trace`）は軽量で依存が少ない。OTel が無効なときでも `trace.get_current_span()` は no-op スパンを返すため、常時インポートしても問題ない
- `opentelemetry-sdk` / `exporter` / `instrumentation` は起動コストが高く、OTel が無効なときは不要なため、有効なときだけ遅延インポートする

------

## 関連ドキュメント

- [13_SetupOTelInstrumentation.md](../13_SetupOTelInstrumentation.md) — ハンズオン手順
- [00_Glossary.md](./00_Glossary.md) — 用語集（trace / span / context propagation / redaction processor）
- [01_LocalStartup.md](./01_LocalStartup.md) — パターン 4（OTel あり起動）
