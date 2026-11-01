# 04 Client And Token Roles

## 目的

このドキュメントは、`demo-web`、`demo-bff`、role、claim、token の関係を整理するものである。

------

## Client の役割

- client は Keycloak を利用するアプリケーション側の設定単位である
- user や role とは別物で、「どのアプリ向けに token を発行するか」を client 単位で管理する
- 今回の repo では `demo-web` と `demo-bff` が主要な client である

まず「client はアプリ」「user は利用者」「role は権限」と分けて考えると追いやすい。

------

## `demo-web` と `demo-bff` の違い

- `demo-web`
  - `docs/04` で token 比較に使った学習用 client
  - public client 寄りで、Keycloak GUI 上の動きや token 差分を見る材料になっている
- `demo-bff`
  - `docs/05` と `docs/06` で FastAPI BFF が使う client
  - confidential client として扱い、`client secret` を使って token 交換する

見方としては、`demo-web` は「Keycloak 側の見え方を学ぶ client」、`demo-bff` は「アプリ実装から実際に使う client」である。

------

## Realm Role と Token の関係

- realm role は realm 全体で共通に使う権限ラベルである
- 今回の repo では `viewer` と `admin` を realm role として使っている
- role そのものは Keycloak の設定であり、token には claim として表現される
- Keycloak では `realm_access.roles` のような形で access token に出てくることがある

重要なのは、role と claim は同じではないという点である。

- role
  - Keycloak 内の認可設定
- claim
  - token の中に出てくる項目

role を割り当てた結果として claim に role 情報が現れる、と考えると分かりやすい。

------

## `alice` と `bob` の差分

- `alice`
  - `viewer` を持つ user
  - `docs/05` では `/admin` で `403`
  - `docs/06` では `/api/admin-data` で `403`
- `bob`
  - `admin` を持つ user
  - `docs/05` では `/admin` に到達できる
  - `docs/06` では `/api/admin-data` に到達できる

この差分により、同じ client を使っても user ごとに認可結果が変わることを確認できる。

Keycloak GUI では、次を比べると追いやすい。

- `Users > alice / bob > Role mappings`
- `Clients > <client> > Client scopes > Evaluate`

------

## Access Token で API が見ているもの

- 署名が正しいか
- `iss` が期待した Keycloak realm か
- `exp` が期限切れでないか
- `aud` が自分のサービス宛てか（`docs/08` で追加）
- role claim に必要な権限が含まれているか

`docs/06` の Backend API は、主に access token を見て JWT 検証と role 判定を行う。

各 claim の意味と検証順序の詳細は [05_TokenClaimsAndValidation.md](./05_TokenClaimsAndValidation.md) を参照する。

ここで大事なのは、API が見ているのは BFF の session ではなく access token だという点である。

- Browser と BFF の間
  - Cookie / session
- BFF と Backend API の間
  - Bearer access token

そのため、`/me` と `/api/me` は似ていても見ている対象が異なる。

------

## 今後の拡張ポイント

- `aud` 検証を追加する
- refresh token と token lifecycle を整理する
- client role と realm role の使い分けを試す
- client scope / mapper を使って token の中身を変える
- public client と PKCE の組み合わせを別パターンとして試す

特に public / confidential client と PKCE の違いは、今後 Next.js や SPA 構成へ広げるときの土台になる。

------

## 関連ドキュメント

- [04_SetupKeycloak.md](../04_SetupKeycloak.md)
- [05_SetupFastAPI-OIDCLogin.md](../05_SetupFastAPI-OIDCLogin.md)
- [06_SetupFastAPI-BackendAPI.md](../06_SetupFastAPI-BackendAPI.md)
