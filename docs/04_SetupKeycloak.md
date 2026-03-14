# Setup Keycloak

## 目的

このドキュメントは、IAM Study Lab の学習用環境で Keycloak の管理コンソールを使い、基本的な認証・認可設定を作成する手順を記録するものである。  
主な目的は以下の通り。

- `lab` realm を作成し、認証設定を分けて管理できる状態にする
- `User`、`Role`、`Client` を管理画面で作成する
- `alice` と `bob` に異なる role を割り当てる
- token に user ごとの認可情報が含まれることを確認する

### 用語

- Realm: ユーザー、role、client、認証設定をまとめて分離する管理単位
- Realm Role: realm 全体で使う権限ラベル。ユーザーへ割り当てて認可に利用する
- User: 認証対象となる利用者そのもの
- Client: Keycloak を利用するアプリケーション側の設定単位
- Access Token: 認証結果と認可情報をアプリケーションへ渡す token
- claim: token 内に含まれる属性情報。`sub` や `preferred_username` などが該当する

------

## 実施概要

今回のセットアップでは、以下の流れで作業を進める。

1. 管理コンソールへログインし、`lab` realm を作成する
2. `viewer` と `admin` の realm role を作成する
3. `alice` と `bob` の user を作成し、初期パスワードを設定する
4. `alice` に `viewer`、`bob` に `admin` を割り当てる
5. `demo-web` client を作成する
6. token 評価画面で `alice` と `bob` の access token を比較する

------

## 前提確認

この手順を始める前に、Keycloak の管理コンソールへアクセスできることを確認する。  
URL は `http://localhost:8080` を想定し、管理者ユーザーには `infra/keycloak/.env` で設定した初期管理者アカウントを利用する。

### 前提確認時の状態

- Keycloak コンテナが起動している
- 管理コンソールが表示できる
- 管理者ユーザーで `master` realm にログインできる

### 前提確認の判定

- `http://localhost:8080` にアクセスして Keycloak 管理コンソールが開く
- 初期管理者ユーザーでログインできる

------

## `lab` Realm の作成

Keycloak 管理コンソールへログインしたら、左上の realm 切り替えメニューから `Create realm` を選択し、`lab` という名前の realm を作成する。

実施手順:

1. 左上の現在の realm 名をクリックする
2. `Create realm` を選択する
3. `Realm name` に `lab` を入力する
4. `Create` を押す

作成後に左上の realm 表示が `lab` になっていれば、以降の設定は `lab` realm に対して行われる。

### `lab` Realm の作成の補足

- Realm は認証設定の境界であり、別 realm にすると user や role も別管理になる
- 学習用途では 1 つの realm から始めると確認しやすい

### `lab` Realm の作成完了時の状態

`lab` という新しい realm が作成され、Keycloak の中に学習用の独立した設定空間ができた。

### `lab` Realm の作成の判定

- 左上の realm 表示が `lab` になっている
- realm 一覧に `lab` が存在する

------

## Realm Role の作成

`lab` realm で利用する認可情報として、`viewer` と `admin` の 2 つの realm role を作成する。

実施手順:

1. 左メニューの `Realm roles` を開く
2. `Create role` を押す
3. `Role name` に `viewer` を入力して保存する
4. 同じ手順で `admin` も作成する

### Realm Role の作成の補足

- role は「誰か」を表すものではなく、「何をしてよいか」を表す
- 今回は realm 全体で使う role を学ぶため、client role ではなく realm role を使う

### Realm Role の作成完了時の状態

`lab` realm 内で、閲覧向けの `viewer` と管理向けの `admin` を認可ラベルとして使える状態になった。

### Realm Role の作成の判定

- `Realm roles` 一覧に `viewer` が存在する
- `Realm roles` 一覧に `admin` が存在する

------

## User の作成

次に、利用者として `alice` と `bob` の 2 人を作成し、それぞれに初期パスワードを設定する。

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

### User の作成の補足

- `Temporary` を `OFF` にすると、初回ログイン時のパスワード変更を必須にしない
- 今回は学習用のため、まず動作確認を優先して `Temporary OFF` で進める

### User の作成完了時の状態

`lab` realm に `alice` と `bob` が作成され、それぞれがログイン可能な資格情報を持つ状態になった。

### User の作成の判定

- `Users` 一覧に `alice` が存在する
- `Users` 一覧に `bob` が存在する
- それぞれの `Credentials` でパスワードが設定済みになっている

------

## User への Role 割り当て(Role mapping)

作成した role を各 user に割り当て、同じ realm 内でも認可を変えられるようにする。

実施手順:

1. `Users > alice` を開く
2. `Role mapping` または `Role mappings` を開く
3. `Assign role` を押す
4. `viewer` を選択して割り当てる
5. `Users > bob` を開く
6. 同様に `admin` を割り当てる

### User への Role 割り当ての補足

- `alice` は「閲覧できる人」、`bob` は「管理できる人」という想定である
- この設定により、user ごとの認可の差を token で確認しやすくなる
- `Assign role` 画面では、`Filter by clients`を`Filter by realm　roles` に切り替えないと作成した realm role が表示されない点に注意する。

### User への Role 割り当て完了時の状態

`alice` には `viewer`、`bob` には `admin` が割り当てられ、同じ realm 内でも異なる権限セットを持つ状態になった。

### User への Role 割り当ての判定

- `alice` の role 一覧に `viewer` が表示される
- `bob` の role 一覧に `admin` が表示される

------

## `demo-web` Client の作成

Keycloak を利用するアプリケーションとして、`demo-web` という OIDC client を 1 つ作成する。

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

### `demo-web` Client の作成の補足

- `Client authentication OFF` は public client として扱うための設定である
- `Standard flow` は一般的なブラウザログインで使われる基本フローである
- `http://localhost/*` は学習用の簡易設定である

### `demo-web` Client の作成完了時の状態

`demo-web` という client が作成され、Keycloak が「どのアプリ向けに token を出すか」を識別できる状態になった。

### `demo-web` Client の作成の判定

- `Clients` 一覧に `demo-web` が存在する
- `demo-web` の設定で `Client type` が `OpenID Connect` になっている
- `Client authentication` が `OFF` である
- `Standard flow` が `ON` である

------

## Token 評価で `alice` と `bob` を比較

最後に、`demo-web` 向けの access token を user ごとに評価し、認証結果と認可情報の違いが token にどう現れるかを確認する。

実施手順:

1. `Clients > demo-web` を開く
2. `Client scopes` を開く
3. `Evaluate` を選ぶ
4. `User` に `alice` を選択する
5. `Generated access token` を表示する
6. `User` を `bob` に切り替えて、同じく access token を表示する

比較する主な claim は以下の通り。

- `sub`
- `preferred_username`
- `azp`
- `realm_access.roles`

期待する見え方の例:

~~~text
alice の access token
- sub: alice 固有の UUID
- preferred_username: alice
- azp: demo-web
- realm_access.roles: default-roles-lab, offline_access, uma_authorization, viewer

bob の access token
- sub: bob 固有の UUID
- preferred_username: bob
- azp: demo-web
- realm_access.roles: default-roles-lab, offline_access, uma_authorization, admin
~~~

### Token 評価の補足

- `sub` は user ごとに異なる識別子であり、同じ username 文字列よりも機械的な識別に向いている
- `preferred_username` は表示上の username に近い値である
- `azp` はその token がどの client 向けに発行されたかを示す
- `realm_access.roles` には既定 role が含まれることがあるため、差分として `viewer` と `admin` に注目すると理解しやすい

### Token 評価後の状態

`alice` と `bob` に対して、同じ `demo-web` client 向けでも異なる role を含む token が生成されることを確認できた。

### Token 評価の判定

- `alice` の token に `preferred_username: alice` が含まれる
- `bob` の token に `preferred_username: bob` が含まれる
- 両者の `azp` が `demo-web` である
- `alice` の `realm_access.roles` に `viewer` が含まれる
- `bob` の `realm_access.roles` に `admin` が含まれる

### 比較結果

[MEMO_CompareTokensUsers.md](../notes/03_Keycloak/MEMO_CompareTokensUsers.md)

------

## この手順で確認できたこと

今回の手順により、以下を確認できた。

- `Realm` を作成して設定を分けられること
- `User` と `Role` を組み合わせて user ごとに認可を変えられること
- `Client` を作成して token 発行先のアプリケーションを定義できること
- token の `realm_access.roles` に user ごとの差分が現れること

この時点では、Keycloak の管理画面上で基本設定と token 内容の確認まで完了している。  
実際のアプリケーションからログインして token を利用する確認は、次の手順で進める想定である。

------

## 本ドキュメントで完了したこと

以下が完了した状態になった。

- `lab` realm の作成
- `viewer` と `admin` の realm role 作成
- `alice` と `bob` の user 作成とパスワード設定
- user への role 割り当て
- `demo-web` client の作成
- token 評価画面での user ごとの差分確認

つまり、Keycloak の管理画面だけで、認証・認可の基本要素を一通り作成して確認できる状態が整った。

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

以下を満たしたため、Keycloak 管理コンソールを使った基本設定の初期導入は完了とする。

- `lab` realm が作成されている
- `viewer` と `admin` の realm role が存在する
- `alice` と `bob` の user が存在し、パスワードが設定されている
- `alice` に `viewer`、`bob` に `admin` が割り当てられている
- `demo-web` client が `OpenID Connect` の public client として作成されている
- token 評価画面で `alice` と `bob` の `realm_access.roles` の差分を確認できる

------

## 関連ドキュメント

- [docs/README.md](./README.md)
- [03_SetupDocker-Keycloak.md](./03_SetupDocker-Keycloak.md)
- [MEMO_CompareTokensUsers.md](../notes/03_Keycloak/MEMO_CompareTokensUsers.md)

------

## まとめ

今回のセットアップで、Keycloak の管理コンソールだけを使って realm、role、user、client を作成し、token に認可情報が含まれる流れを整理できた。  
今後はこの設定を土台にして、実際のアプリケーションからログインを行い、token を受け取って認可判定へつなげる検証を進めていく予定である。
