# Setup Client Scope と Mapper

## ここでのゴール

この手順では、Keycloak の client scope と mapper の仕組みを体験し、次の状態に到達することをゴールとする。

- shared client scope を作成して `demo-bff` に割り当てられる
- User Property Mapper / Hardcoded Claim Mapper / Role Name Mapper を使って、access token に独自の claim を追加できる
- optional scope を作成し、scope パラメータで明示要求したときだけ claim が出ることを確認できる
- Token Evaluate で各 mapper の効果を確認できる

必要な用語は [00_Glossary.md](./Reference/00_Glossary.md) を参照する。

------

## 前提確認

この手順を始める前に、以下が完了していることを確認する。

- `docs/08_SetupAudienceValidation.md` の手順が完了している
- Keycloak が `http://localhost:8080` で起動している
- `demo-bff` client が `lab` realm に存在する

判定:

- `http://localhost:8080` の管理コンソールにログインできる
- `alice` でログインして `http://localhost:8000/api/me` が `200` を返す

------

## この手順の流れ

この手順では、以下の流れで進める。

1. client scope の種類（shared / dedicated、default / optional）を整理する
2. shared default scope `demo-shared-claims` を作成して `demo-bff` に割り当てる
3. User Property Mapper を追加して `lab_username` claim を出す
4. Hardcoded Claim Mapper を追加して `app_env` claim を出す
5. Role Name Mapper を追加して `admin` を `lab-admin` に変換する
6. Token Evaluate で各 mapper の効果を確認する
7. optional scope `demo-optional-claims` を作成し、scope 指定の有無で挙動が変わることを確認する
8. 失敗例を再現する

------

## client scope の種類

Keycloak の client scope には「共有範囲」と「付与タイミング」の2つの軸がある。

| 軸         | 種別      | 説明                                              |
|------------|-----------|--------------------------------------------------|
| 共有範囲   | shared    | 複数の client に割り当てられる再利用可能な scope   |
| 共有範囲   | dedicated | 特定の client 専用の scope（`xxx-dedicated`）      |
| 付与タイミング | default   | scope パラメータを問わず自動付与される        |
| 付与タイミング | optional  | scope パラメータで名前を指定したときだけ付与される |

client scope の役割は「mapper をまとめる箱」である。scope に mapper を追加して client に割り当てることで、その client の token に claim が付与される。

補足:

- `demo-bff-dedicated` は Keycloak が `demo-bff` 作成時に自動生成した dedicated scope である
- 今回作成する `demo-shared-claims` は shared scope として、複数の client で再利用できる形にする

### 今回の構成における scope と mapper の関係

~~~text
client: demo-bff（割り当てたスコープが token の中身を決める）
│
├─ scope: demo-shared-claims  [Default / shared]
│    ├─ map-username         (User Property)   → lab_username
│    ├─ hardcoded-app-env    (Hardcoded Claim) → app_env=lab
│    └─ rename-admin-role    (Role Name)       → admin→lab-admin
│
├─ scope: demo-optional-claims  [Optional]
│    └─ hardcoded-feature-flag (Hardcoded Claim) → feature_x_enabled
│
└─ scope: demo-bff-dedicated  [dedicated]
     └─ add-demo-api-audience (Audience)        → aud: demo-api
~~~

default scope が付いた場合のトークン（`demo-shared-claims` が自動付与される）:

~~~text
{
  "iss": "http://localhost:8080/realms/lab",
  "aud": ["account", "demo-api"],          // add-demo-api-audience の効果
  "azp": "demo-bff",
  "preferred_username": "bob",
  "lab_username": "bob",                   // map-username の効果
  "app_env": "lab",                        // hardcoded-app-env の効果
  "realm_access": {
    "roles": ["lab-admin", ...]            // rename-admin-role の効果（admin → lab-admin）
  },
  "scope": "openid profile email demo-shared-claims"
}
~~~

optional scope を明示要求した場合（`scope=openid demo-optional-claims` を追加）:

~~~text
{
  ...
  "feature_x_enabled": true,              // hardcoded-feature-flag の効果
  "scope": "openid profile email demo-shared-claims demo-optional-claims"
}
~~~

------

## Shared scope `demo-shared-claims` の作成

新しい shared client scope を作成する。

実施手順:

1. `http://localhost:8080` の管理コンソールを開く
2. 左上で `lab` realm を選ぶ
3. 左メニューの `Client Scopes` を開く
4. `Create client scope` をクリックする
5. 以下の値を入力して保存する

~~~text
Name:                   demo-shared-claims
Type:                   Default
Display on consent:     OFF
Include in token scope: ON
~~~

判定:

- `Client Scopes` 一覧に `demo-shared-claims` が表示される
- `Type` が `Default` になっている

補足:

- `Type: Default` は「この scope を client に割り当てたとき、scope パラメータなしで自動付与される」という意味である
- `Include in token scope: ON` にすると、access token の `scope` クレームにも scope 名が現れる

------

## `demo-bff` への scope 割り当て

作成した `demo-shared-claims` を `demo-bff` client に割り当てる。

実施手順:

1. 左メニューの `Clients` を開く
2. `demo-bff` を選ぶ
3. `Client scopes` タブを開く
4. `Add client scope` をクリックする
5. 一覧から `demo-shared-claims` を選び、`Default` を選択して `Add` をクリックする

判定:

- `demo-bff` の client scopes 一覧に `demo-shared-claims` が `Default` として表示される

------

## User Property Mapper の追加

`demo-shared-claims` scope に User Property Mapper を追加して、access token に `lab_username` claim を出す。

User Property とは Keycloak のユーザー属性（`username`、`email`、`firstName` など）のことである。

実施手順:

1. 左メニューの `Client Scopes` から `demo-shared-claims` を開く
2. `Mappers` タブを開く
3. `Add mapper` から `By configuration` を選ぶ
4. 一覧から `User Property` を選ぶ
5. 以下の値を入力して保存する

~~~text
Name:                map-username
Property:            username
Token Claim Name:    lab_username
Claim JSON Type:     String
Add to access token: ON
Add to ID token:     OFF
~~~

判定:

- `demo-shared-claims` の mapper 一覧に `map-username` が表示される

補足:

- `Property` には Keycloak のユーザーモデルのフィールド名（`username`、`email`、`firstName` など）を指定する
- `Add to ID token: OFF` にすることで、access token にだけ付与できる
- `Add to lightweight access token` / `Add to userinfo` / `Add to token introspection` は OFF のままでよい

------

## Hardcoded Claim Mapper の追加

`demo-shared-claims` scope に Hardcoded Claim Mapper を追加して、access token に固定値 `app_env: lab` を出す。

実施手順:

1. `demo-shared-claims` の `Mappers` タブを開く
2. `Add mapper` から `By configuration` を選ぶ
3. 一覧から `Hardcoded claim` を選ぶ
4. 以下の値を入力して保存する

~~~text
Name:                hardcoded-app-env
Token Claim Name:    app_env
Claim Value:         lab
Claim JSON Type:     String
Add to access token: ON
Add to ID token:     OFF
~~~

判定:

- `demo-shared-claims` の mapper 一覧に `hardcoded-app-env` が表示される

補足:

- Hardcoded Claim はユーザーに関わらず常に同じ値を token に埋めたい場合に使う
- 環境識別子（`lab`、`staging`、`prod`）やサービス名を入れるユースケースが多い
- `Add to lightweight access token` / `Add to userinfo` / `Add to token introspection` は OFF のままでよい

------

## Role Name Mapper の追加

`demo-shared-claims` scope に Role Name Mapper を追加して、realm role `admin` を token 内で `lab-admin` に変換する。

実施手順:

1. `demo-shared-claims` の `Mappers` タブを開く
2. `Add mapper` から `By configuration` を選ぶ
3. 一覧から `Role Name Mapper` を選ぶ
4. 以下の値を入力して保存する

~~~text
Name:          rename-admin-role
Role:          admin
New Role Name: lab-admin
~~~

判定:

- `demo-shared-claims` の mapper 一覧に `rename-admin-role` が表示される

補足:

- Role Name Mapper は token 上のロール名を変換するが、Keycloak 内部のロール定義は変わらない
- `Role` フィールドには realm role 名を入力する（`クライアント名.ロール名` の形式で client role も指定できる）
- `admin` role を持つユーザーの token だけ変換が起きる。`admin` role を持たないユーザーには影響しない
- `Add to lightweight access token` / `Add to userinfo` / `Add to token introspection` は OFF のままでよい
- この Mapper は shared scope に紐づいているため、Backend API など role 名を参照しているコードがあると挙動が変わる点に注意する
- 動作確認後は `rename-admin-role` を削除して元に戻す。Backend API と BFF は `admin` を参照しており、Mapper を残したまま次の手順に進むと 403 が継続する

------

## Token Evaluate で効果を確認する

Keycloak の Token Evaluate 画面で、追加した各 mapper の効果を確認する。

### alice で確認する（viewer role のみ / admin role なし）

確認手順:

1. 左メニューの `Clients > demo-bff` を開く
2. `Client scopes` タブ → `Evaluate` を開く
3. `User` に `alice` を選ぶ
4. `Generated access token` を展開する

期待する見え方:

~~~text
"lab_username": "alice",
"app_env": "lab",
~~~

- `alice` は `admin` role を持たないため、`lab-admin` は `realm_access.roles` に現れない
- `viewer` role は Role Name Mapper の変換対象外なので、そのまま `viewer` として残る

### bob で確認する（admin role あり）

確認手順:

1. `User` を `bob` に切り替える
2. `Generated access token` を展開する

期待する見え方:

~~~text
"lab_username": "bob",
"app_env": "lab",
"realm_access": {
  "roles": ["lab-admin", "default-roles-lab", ...]
}
~~~

- `bob` の `admin` role が `lab-admin` に変換されている
- `default-roles-lab` などのデフォルト role は変換対象外のため、そのまま残る

判定:

- `alice` の token に `lab_username: "alice"` と `app_env: "lab"` が含まれる
- `bob` の token の `realm_access.roles` に `lab-admin` が含まれる
- `alice` の token の `realm_access.roles` には `lab-admin` が含まれない

------

## Optional scope の作成と明示要求

optional scope を作成し、scope パラメータで明示要求したときだけ claim が付与されることを確認する。

### optional scope `demo-optional-claims` の作成

実施手順:

1. 左メニューの `Client Scopes` → `Create client scope` を開く
2. 以下の値を入力して保存する

~~~text
Name:                   demo-optional-claims
Type:                   None
Include in token scope: ON
~~~

3. 保存後、`Mappers` タブを開く
4. `Add mapper` から `By configuration` → `Hardcoded claim` を選ぶ
5. 以下の値を入力して保存する

~~~text
Name:                hardcoded-feature-flag
Token Claim Name:    feature_x_enabled
Claim Value:         true
Claim JSON Type:     boolean
Add to access token: ON
Add to ID token:     OFF
~~~

補足:

- `Type` を `Optional` にすると Token Evaluate の Scope フィールドのドロップダウンに表示されず、手動入力しても token に反映されない
- `Type: None` にすることで Token Evaluate で確認できる状態になる（client scopes 一覧では `Optional` と表示される）

### `demo-bff` への optional scope 割り当て

実施手順:

1. 左メニューの `Clients > demo-bff` を開く
2. `Client scopes` タブ → `Add client scope` をクリックする
3. 一覧から `demo-optional-claims` を選ぶ
4. `Optional` を選択して `Add` をクリックする

判定:

- `demo-bff` の client scopes 一覧に `demo-optional-claims` が `Optional` として表示される

### Token Evaluate で scope 指定の有無を比較する

確認手順（scope パラメータなし）:

1. `Clients > demo-bff > Client scopes > Evaluate` を開く
2. `User` に `alice` を選ぶ
3. `Scope` フィールドは空のまま評価する
4. `Generated access token` を展開する

期待する見え方:

- `feature_x_enabled` が token に含まれない

確認手順（scope パラメータあり）:

1. `Scope` フィールドに `demo-optional-claims` を入力する
2. `Generated access token` を展開する

期待する見え方:

~~~text
"feature_x_enabled": true,
~~~

判定:

- scope 未指定では `feature_x_enabled` が token に現れない
- scope に `demo-optional-claims` を指定すると `feature_x_enabled: true` が現れる

------

## 失敗例

### 失敗例 1: scope を `demo-bff` に割り当て忘れる

目的:

scope が未割り当ての場合、mapper を追加しても token に claim が出ないことを確認する。

再現方法:

1. `Clients > demo-bff > Client scopes` で `demo-shared-claims` の行を選択し、`Remove` する
2. Token Evaluate で `alice` の token を確認する

期待する見え方:

- `lab_username` と `app_env` が token に含まれない

補足:

- mapper を追加しても、scope が client に割り当てられていなければ token に反映されない
- 確認後、`demo-shared-claims` を `Default` で再割り当てして元に戻す

------

### 失敗例 2: optional scope を scope パラメータなしで要求する

目的:

optional scope は scope パラメータで明示要求しなければ、token に付与されないことを確認する。

再現方法:

1. Token Evaluate を開く
2. `User` に `alice` を選ぶ
3. `Scope` フィールドに `demo-optional-claims` を指定せずに評価する

期待する見え方:

- `feature_x_enabled` が token に含まれない

補足:

- optional scope は「使う側が明示的に要求するもの」であり、黙って付与はされない
- 実際の認可リクエスト（BFF からの OAuth2 フロー）では、`scope=openid demo-optional-claims` のように追記する必要がある

------

### 失敗例 3: shared scope の変更が他の client にも波及する

目的:

shared scope を変更すると、その scope を割り当てている全 client の token に影響することを確認する。

再現方法:

1. 左メニューの `Client Scopes > demo-shared-claims > Mappers` を開く
2. `hardcoded-app-env` の `Claim Value` を `lab` から `production` に変更する
3. `demo-bff` の Token Evaluate で `alice` の token を確認する

期待する見え方:

- `app_env: "production"` に変わっている

補足:

- dedicated scope（`demo-bff-dedicated` など）であれば1つの client 専用だが、shared scope は割り当てた全 client に波及する
- shared scope の mapper を変更する際は、影響範囲を事前に確認する
- 確認後、`Claim Value` を `lab` に戻す

------

## 完了判定

- `Client Scopes` 一覧に `demo-shared-claims`（Default）と `demo-optional-claims`（Optional）が存在する
- `demo-bff` の client scopes に `demo-shared-claims`（Default）と `demo-optional-claims`（Optional）が割り当てられている
- `demo-shared-claims` に `map-username`、`hardcoded-app-env`、`rename-admin-role` の3つの mapper が追加されている
- `demo-optional-claims` に `hardcoded-feature-flag` mapper が追加されている
- Token Evaluate（alice）で `lab_username: "alice"` と `app_env: "lab"` が確認できる
- Token Evaluate（bob）で `realm_access.roles` に `lab-admin` が含まれる
- Token Evaluate で scope に `demo-optional-claims` を指定すると `feature_x_enabled: true` が現れる
- scope 指定なしでは `feature_x_enabled` が現れない

------

## まとめ

今回の手順で確認したこと:

- client scope は「mapper をまとめる箱」であり、client に割り当てることで token への claim 付与が有効になる
- User Property Mapper でユーザーのプロパティ（`username`）を独自 claim として token に出せる
- Hardcoded Claim Mapper で固定値を全ユーザーの token に埋め込める
- Role Name Mapper でトークン上のロール名を変換できる（Keycloak 内部のロール定義は変わらない）
- shared scope は複数の client で再利用でき、変更が割り当て済みの全 client に波及する
- optional scope は scope パラメータで明示要求したときだけ付与される

ここまでで、Keycloak の client scope と mapper を組み合わせて、token の中身を柔軟に制御できることを確認できた。  
次は JWT のエッジケーステストで、実装した検証ロジックの堅牢性を確認する。

------

## 関連ドキュメント

- [08_SetupAudienceValidation.md](./08_SetupAudienceValidation.md) を参照
- [Reference/06_ClientScopeAndMapperTypes.md](./Reference/06_ClientScopeAndMapperTypes.md) — mapper の種別カタログと設計指針
- [Reference/04_ClientAndTokenRoles.md](./Reference/04_ClientAndTokenRoles.md) を参照
- [Reference/00_Glossary.md](./Reference/00_Glossary.md) を参照
