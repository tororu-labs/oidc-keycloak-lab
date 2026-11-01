# Setup Keycloak

## ここでのゴール

この手順では、Keycloak の管理コンソールを使って基本的な認証・認可設定を作成し、次の状態に到達することをゴールとする。

- `lab` realm を作成し、認証設定を分けて管理できるようにする
- `viewer` と `admin` の realm role を作成する
- `alice` と `bob` を作成し、異なる role を割り当てる
- `demo-web` client を作成し、token の差分を確認できるようにする

必要な用語は [00_Glossary.md](Reference/00_Glossary.md) を参照する。

------

## 前提確認

この手順を始める前に、Keycloak の管理コンソールへアクセスできることを確認する。  
URL は `http://localhost:8080` を想定し、管理者ユーザーには `infra/keycloak/.env` で設定した初期管理者アカウントを利用する。

判定:

- `http://localhost:8080` にアクセスして Keycloak 管理コンソールが開く
- 初期管理者ユーザーでログインできる

------

## この手順の流れ

この手順では、以下の流れで進める。

1. `lab` realm を作成する
2. `viewer` と `admin` の realm role を作成する
3. `alice` と `bob` の user を作成し、初期パスワードを設定する
4. `alice` に `viewer`、`bob` に `admin` を割り当てる
5. `demo-web` client を作成する
6. token 評価画面で `alice` と `bob` の access token を比較する

------

## `lab` Realm の作成

Keycloak 管理コンソールへログインしたら、左上の realm 切り替えメニューから `Create realm` を選択し、`lab` という名前の realm を作成する。

実施手順:

1. 左上の現在の realm 名をクリックする
2. `Create realm` を選択する
3. `Realm name` に `lab` を入力する
4. `Create` を押す

判定:

- 左上の realm 表示が `lab` になっている
- realm 一覧に `lab` が存在する

完了時の状態:

`lab` という新しい realm が作成され、学習用の独立した設定空間ができる。

補足:

- realm が違うと user や role も別管理になる

------

## Realm Role の作成

`lab` realm で利用する認可情報として、`viewer` と `admin` の 2 つの realm role を作成する。

実施手順:

1. 左メニューの `Realm roles` を開く
2. `Create role` を押す
3. `Role name` に `viewer` を入力して保存する
4. 同じ手順で `admin` も作成する

判定:

- `Realm roles` 一覧に `viewer` が存在する
- `Realm roles` 一覧に `admin` が存在する

完了時の状態:

`lab` realm 内で、閲覧向けの `viewer` と管理向けの `admin` を認可ラベルとして使える。

補足:

- role や token の関係は [04_ClientAndTokenRoles.md](Reference/04_ClientAndTokenRoles.md) を参照する

------

## User の作成

利用者として `alice` と `bob` の 2 人を作成し、それぞれに初期パスワードを設定する。

### `alice` の作成

1. 左メニューの `Users` を開く
2. `Add user` を押す
3. `Username` に `alice` を入力する
4. 必要に応じて `Email` や `First name` を入力する
5. `Create` または `Save` を押す
6. 作成後に `Credentials` タブを開く
7. `Set password` を押す
8. 初期パスワードを入力し、`Temporary` を `OFF` にして保存する

### `bob` の作成

`alice` と同じ手順で `bob` を作成し、初期パスワードを設定する。

判定:

- `Users` 一覧に `alice` が存在する
- `Users` 一覧に `bob` が存在する
- それぞれの `Credentials` でパスワードが設定済みになっている

完了時の状態:

`lab` realm に `alice` と `bob` が作成され、それぞれがログイン可能な資格情報を持つ。

補足:

- 学習用のため、`Temporary` は `OFF` にして進める

------

## User への Role 割り当て

作成した role を各 user に割り当て、同じ realm 内でも認可を変えられるようにする。

実施手順:

1. `Users > alice` を開く
2. `Role mapping` または `Role mappings` を開く
3. `Assign role` を押す
4. `viewer` を選択して割り当てる
5. `Users > bob` を開く
6. 同様に `admin` を割り当てる

判定:

- `alice` の role 一覧に `viewer` が表示される
- `bob` の role 一覧に `admin` が表示される

完了時の状態:

`alice` には `viewer`、`bob` には `admin` が割り当てられ、user ごとの認可差分を確認できる状態になる。

補足:

- `Assign role` 画面では、`Filter by realm roles` に切り替えないと作成した realm role が表示されないことがある

------

## `demo-web` Client の作成

Keycloak を利用するアプリケーションとして、`demo-web` という OIDC client を作成する。

実施手順:

1. 左メニューの `Clients` を開く
2. `Create client` を押す
3. `Client type` で `OpenID Connect` を選ぶ
4. `Client ID` に `demo-web` を入力する
5. 次へ進み、`Client authentication` を `OFF` にする
6. `Standard flow` が `ON` になっていることを確認する
7. 保存する

必要に応じてログイン設定の入力欄が表示された場合は、学習用として以下を設定する。

~~~text
Root URL: http://localhost
Home URL: http://localhost/
Valid redirect URIs: http://localhost/*
Valid post logout redirect URIs: http://localhost/*
~~~

判定:

- `Clients` 一覧に `demo-web` が存在する
- `demo-web` の設定で `Client type` が `OpenID Connect` になっている
- `Client authentication` が `OFF` である
- `Standard flow` が `ON` である

完了時の状態:

`demo-web` という client が作成され、Keycloak が token 発行先のアプリケーションを識別できる状態になる。

補足:

- `demo-web` と `demo-bff` の違いは [04_ClientAndTokenRoles.md](Reference/04_ClientAndTokenRoles.md) を参照する

------

## Token 評価で `alice` と `bob` を比較

`demo-web` 向けの access token を user ごとに評価し、認証結果と認可情報の違いが token にどう現れるかを確認する。

実施手順:

1. `Clients > demo-web` を開く
2. `Client scopes` を開く
3. `Evaluate` を選ぶ
4. `User` に `alice` を選択する
5. `Generated access token` を表示する
6. `User` を `bob` に切り替えて、同じく access token を表示する

期待する見え方の例:

~~~text
alice の access token
- preferred_username: alice
- azp: demo-web
- realm_access.roles: ... viewer

bob の access token
- preferred_username: bob
- azp: demo-web
- realm_access.roles: ... admin
~~~

判定:

- `alice` の token に `preferred_username: alice` が含まれる
- `bob` の token に `preferred_username: bob` が含まれる
- 両者の `azp` が `demo-web` である
- `alice` の `realm_access.roles` に `viewer` が含まれる
- `bob` の `realm_access.roles` に `admin` が含まれる

補足:

- token、role、claim の関係は [04_ClientAndTokenRoles.md](Reference/04_ClientAndTokenRoles.md) を参照する

------

## 実行コマンド一覧

本ドキュメント自体は管理コンソールでの操作が中心であり、新しいコマンド実行は必須ではない。  
前提確認として利用する場合のコマンドのみ以下に記載する。

### Keycloak 起動確認

~~~zsh
docker compose -f infra/keycloak/docker-compose.yml up -d # Keycloak と PostgreSQL を起動
docker compose -f infra/keycloak/docker-compose.yml ps # 起動状態を確認
~~~

------

## 完了判定

- `lab` realm が作成されている
- `viewer` と `admin` の realm role が存在する
- `alice` と `bob` の user が存在し、パスワードが設定されている
- `alice` に `viewer`、`bob` に `admin` が割り当てられている
- `demo-web` client が `OpenID Connect` の public client として作成されている
- token 評価画面で `alice` と `bob` の `realm_access.roles` の差分を確認できる

------

## まとめ

今回の手順で確認したこと:

- `lab` realm を作成した
- `viewer` と `admin` の realm role を作成した
- `alice` と `bob` を作成し、role を割り当てた
- `demo-web` client を作成し、token の差分を確認した

ここまでで、Keycloak の管理コンソールだけで認証・認可の基本要素を一通り作成して確認できた。  
次は [05_SetupFastAPI-OIDCLogin.md](05_SetupFastAPI-OIDCLogin.md) を参照し、実際の Web アプリからログインして token を利用する流れを確認する。

------

## 関連ドキュメント

- [03_SetupDocker-Keycloak.md](./03_SetupDocker-Keycloak.md) を参照
- [05_SetupFastAPI-OIDCLogin.md](./05_SetupFastAPI-OIDCLogin.md) を参照
- [04_ClientAndTokenRoles.md](./Reference/04_ClientAndTokenRoles.md) を参照
