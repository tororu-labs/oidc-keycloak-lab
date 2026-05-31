# 06 Client Scope And Mapper Types

## 目的

このドキュメントは、Keycloak の client scope と mapper の仕組みを座学として整理するものである。

- client scope の正体と役割
- dedicated scope と shared scope の違い
- default scope と optional scope の動作の違い
- 主要な mapper 種別のカタログ
- OAuth2 の scope と Keycloak の role の関係

`docs/09_SetupClientScopeAndMapper.md` のハンズオンと合わせて読むと理解しやすい。

------

## client scope の正体

client scope は「mapper をまとめる箱」である。scope 単体は token に何も追加しない。scope に mapper を追加し、その scope を client に割り当てることで、はじめて token に claim が付与される。

~~~text
client scope
└── mapper A（lab_username を出す）
└── mapper B（app_env を出す）
└── mapper C（admin を lab-admin に変換する）

client（demo-bff）
└── demo-bff-dedicated（dedicated scope）
└── demo-shared-claims（shared scope）← 上の scope を割り当てた
~~~

この構造により、「mapper の集まり」を複数の client で再利用できるようになっている。

------

## dedicated scope vs shared scope

| 種別 | 説明 | 主な用途 |
|------|------|---------|
| dedicated scope | 特定の client 専用の scope | その client だけに付けたい mapper（例: Audience Mapper） |
| shared scope | 複数の client に割り当てられる scope | 複数 client で同じ claim を出したい mapper の共通置き場 |

Keycloak は client 作成時に `<client名>-dedicated` という dedicated scope を自動生成する。`docs/08` で追加した Audience Mapper はこの dedicated scope に置いている。

shared scope は再利用性が高い反面、mapper を変更すると**割り当てている全 client の token に波及する**。変更前に影響範囲を確認することが重要である。

------

## default scope vs optional scope

| 種別 | 付与タイミング | 使いどころ |
|------|--------------|-----------|
| default scope | scope パラメータを問わず自動付与 | 常に必要な claim（username、環境識別子など） |
| optional scope | scope パラメータで明示要求したときだけ付与 | 特定のフローや機能でのみ必要な claim |

認可リクエストの `scope` パラメータを使って optional scope を要求する例:

~~~text
scope=openid demo-optional-claims
~~~

補足:

- default scope は client に割り当てた時点で常に付与されるため、不要な claim が増えすぎないよう注意する
- optional scope は「使う側が明示的に要求するもの」であり、API や画面の機能単位で分けるとスッキリ整理できる

------

## 主要な mapper 種別カタログ

Keycloak には多くの mapper 種別があるが、実務でよく使うものを以下に整理する。

| mapper 種別 | 何をするか | 主な設定項目 |
|------------|-----------|------------|
| Audience | access token の `aud` に値を追加する | Included Custom Audience |
| User Property | Keycloak ユーザーモデルの属性を claim として出す | Property（`username`、`email` など）、Token Claim Name |
| User Attribute | Keycloak ユーザーのカスタム属性を claim として出す | User Attribute、Token Claim Name |
| Hardcoded Claim | 固定値を token に埋め込む | Token Claim Name、Claim Value、Claim JSON Type |
| Role Name Mapper | token 上のロール名を別の名前に変換する | Role（変換元）、New Role Name（変換先） |
| Group Membership | ユーザーが属するグループのパスを claim として出す | Token Claim Name、Full group path |
| User Realm Role | realm role を token に追加する（デフォルトで存在する） | Token Claim Name（通常は `realm_access.roles`） |
| User Client Role | 特定 client の client role を token に追加する | Client ID、Token Claim Name |

補足:

- `User Property` と `User Attribute` は混同しやすいが、`User Property` は `username`・`email`・`firstName` などの Keycloak 組み込みフィールドを指す。`User Attribute` はユーザー設定画面の `Attributes` タブで追加したカスタムフィールドを指す
- `Role Name Mapper` は token 上の表現を変えるだけで、Keycloak 内部のロール定義は変わらない
- `Group Membership` は `/grp-a/sub-grp` のようなグループパスを出すため、role とは別のグループ構造を claim で表したい場合に使う

------

## OAuth2 の scope と Keycloak の role の関係

OAuth2 の `scope` と Keycloak の `role` は別の概念であり、混同しやすい。

| 概念 | 何を表すか | 例 |
|------|-----------|-----|
| OAuth2 scope | リソースへのアクセス種別・権限委譲の範囲 | `openid`、`profile`、`demo-optional-claims` |
| Keycloak role | user に付与した権限ラベル | `viewer`、`admin` |

**scope** はクライアントが「何の情報・操作へのアクセスを要求するか」を宣言するものである。  
**role** はユーザーが「何をできるか」を定義するものである。

Keycloak ではこの2つを組み合わせて使う。

- scope（`demo-optional-claims`）の付与により、mapper が動いて claim が token に入る
- その claim（`realm_access.roles`）の中に role 情報が含まれる
- API はその role を読んで認可判定を行う

~~~text
認可リクエスト（scope=openid demo-optional-claims）
  ↓
Keycloak が scope に対応した mapper を実行
  ↓
access token に claim が付与される
  ↓
API が claim を読んで認可判定
~~~

補足:

- Keycloak はデフォルトで `openid`・`profile`・`email`・`roles`・`web-origins` などの組み込み scope を持つ
- `roles` scope が有効なとき、realm role や client role が `realm_access.roles` / `resource_access` として token に載る
- scope と role を切り分けて考えると、「どの claim を token に入れるか（scope / mapper の設計）」と「その claim で何を判定するか（アプリの認可ロジック）」が整理しやすくなる

------

## 関連ドキュメント

- [09_SetupClientScopeAndMapper.md](../09_SetupClientScopeAndMapper.md) — client scope と mapper のハンズオン
- [08_SetupAudienceValidation.md](../08_SetupAudienceValidation.md) — Audience Mapper の追加手順
- [04_ClientAndTokenRoles.md](./04_ClientAndTokenRoles.md)
- [05_TokenClaimsAndValidation.md](./05_TokenClaimsAndValidation.md)
- [00_Glossary.md](./00_Glossary.md)
