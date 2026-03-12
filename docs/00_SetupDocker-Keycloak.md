# Setup Docker Keycloak

## 目的

このドキュメントは、IAM Study Lab の環境構築の一環として、Docker を使って Keycloak と PostgreSQL を起動するまでの手順を記録するものである。  
主な目的は以下の通り。

- Docker Desktop をインストールして Docker 環境を整える
- `infra/keycloak/.env` を作成して Keycloak と PostgreSQL の環境変数を定義する
- `infra/keycloak/docker-compose.yml` を作成してコンテナ構成を定義する
- Docker Compose で Keycloak と PostgreSQL のコンテナを起動する
- Keycloak の管理コンソールへアクセスできる状態にする

### 用語

- Docker Desktop: Docker Engine や Docker Compose をローカルで利用するためのアプリケーション
- Docker Compose: 複数コンテナの構成を YAML ファイルで定義し、まとめて起動・停止できる仕組み
- container: アプリケーションを分離された実行環境で動かす単位
- service: Compose 上で定義するコンテナ設定の単位
- volume: コンテナを削除しても保持したいデータを保存する領域
- healthcheck: コンテナが正常に動作しているかを確認するための設定

------

## 実施概要

今回のセットアップでは、以下の流れで作業を進めた。

1. Docker Desktop をインストールして起動確認
2. `infra/keycloak/.env` を作成
3. `infra/keycloak/docker-compose.yml` を作成
4. Docker Compose で Keycloak と PostgreSQL を起動
5. `http://localhost:8080` にアクセスして管理コンソールを確認

------

## Docker Desktop のインストール

Homebrew を使用して Docker Desktop をインストールし、ローカルで Docker コマンドを利用できる状態にした。

~~~zsh
brew install --cask docker
open -a Docker
~~~

Docker Desktop の起動後に、以下のコマンドで利用可能な状態になっていることを確認した。

~~~zsh
docker version
docker compose version
docker run hello-world
~~~

### 判定

`docker version` と `docker compose version` が表示され、`docker run hello-world` が成功したため、Docker 環境は正常に利用できると判断した。

------

## `.env` の作成

Keycloak と PostgreSQL の環境変数を定義するため、Compose ファイルと同じディレクトリに `.env` を作成した。

~~~zsh
mkdir -p infra/keycloak
cat > infra/keycloak/.env <<'EOF'
POSTGRES_DB=keycloak
POSTGRES_USER=keycloak
POSTGRES_PASSWORD=******
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=******
EOF
~~~

この `.env` ファイルには秘密情報が含まれるため、本番環境では環境変数やシークレット管理ツールを使う想定である。今回は学習目的のため、ローカル開発用の簡易構成として扱った。

### この時点の状態

Keycloak と PostgreSQL が参照するデータベース名、接続ユーザー、初期管理者ユーザーの情報をローカルファイルで管理できる状態になった。

------

## `docker-compose.yml` の作成

Keycloak と PostgreSQL のサービス定義をまとめるため、`docker-compose.yml` を作成した。

~~~zsh
mkdir -p infra/keycloak
cat > infra/keycloak/docker-compose.yml <<'EOF'
name: iam-lab-study-keycloak

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 20

  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: ${KC_BOOTSTRAP_ADMIN_USERNAME}
      KC_BOOTSTRAP_ADMIN_PASSWORD: ${KC_BOOTSTRAP_ADMIN_PASSWORD}
      KC_DB: postgres
      KC_DB_URL_HOST: postgres
      KC_DB_URL_PORT: 5432
      KC_DB_URL_DATABASE: ${POSTGRES_DB}
      KC_DB_USERNAME: ${POSTGRES_USER}
      KC_DB_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "127.0.0.1:8080:8080"
    command: start-dev

volumes:
  pgdata:
EOF
~~~

### 補足

- `postgres` サービスは `pgdata` volume を利用し、データベースの内容を永続化する構成にした。
- `keycloak` サービスは `depends_on` と PostgreSQL 側の `healthcheck` を利用し、DB の起動確認後に接続する構成にした。
- `127.0.0.1:8080:8080` を指定することで、Keycloak の管理画面をローカル PC からのみ参照できるようにした。
- `name: iam-lab-study-keycloak` を明示し、このプロジェクトで作られる container・network・volume の名前を判別しやすくした。

### 実施時の状態

`docker compose` コマンドで Keycloak と PostgreSQL をまとめて起動できる設定ファイルが用意できた。

------

## Docker Compose でコンテナを起動

リポジトリのルートディレクトリで、以下のコマンドを実行した。

~~~zsh
docker compose -f infra/keycloak/docker-compose.yml up -d
docker compose -f infra/keycloak/docker-compose.yml ps
~~~

`docker-compose.yml` が `infra/keycloak/` 配下にあるため、リポジトリルートで実行するときは `up` だけでなく `ps` や `down` でも `-f` で対象ファイルを指定する。

今回の Compose ファイルは `name: iam-lab-study-keycloak` を持つため、生成される container・network・volume にはこの project name が接頭辞として付く。

`infra/keycloak` に移動してから実行する場合は、次のコマンドでもよい。

~~~zsh
cd infra/keycloak
docker compose up -d
docker compose ps
~~~

起動時の衝突や既存 resource の扱いについては、`notes/02_DockerKeycloak/00_ComposeFile.md` に整理した。

### コンテナ起動の判定

`docker compose ps` で PostgreSQL コンテナが `healthy` となり、Keycloak コンテナが起動状態になっていれば、Compose による起動は成功と判断した。

------

## 管理コンソールの確認

ブラウザで `http://localhost:8080` にアクセスし、Keycloak の管理コンソールが表示されることを確認した。

### 管理コンソールの判定

- Keycloak の管理コンソールが表示される
- `.env` に設定した初期管理者ユーザーでログインできる
- Keycloak をローカル環境から操作できる状態になっている

------

## 本ドキュメントで完了したこと

以下が完了した状態になった。

- Docker Desktop のインストール
- Keycloak 用 `.env` の作成
- `docker-compose.yml` の作成
- PostgreSQL と Keycloak の起動
- Keycloak 管理コンソールの表示確認

つまり、ローカル環境で Keycloak を使った IAM 検証を始めるための土台ができた。

------

## 実行コマンド一覧

### Docker Desktop 関連

~~~zsh
brew install --cask docker # Docker Desktop のインストール
open -a Docker # Docker Desktop の起動
docker version # Docker の利用確認
docker compose version # Docker Compose の利用確認
docker run hello-world # コンテナ実行確認
~~~

### Keycloak Compose 関連

~~~zsh
mkdir -p infra/keycloak # Keycloak 用ディレクトリの作成
docker compose -f infra/keycloak/docker-compose.yml up -d # コンテナ起動
docker compose -f infra/keycloak/docker-compose.yml ps # 起動状態確認
~~~

------

## 完了判定

以下を満たしたため、Docker を使った Keycloak の初期導入は完了とする。

- `docker version` が成功する
- `docker compose version` が成功する
- `docker run hello-world` が成功する
- `docker compose -f infra/keycloak/docker-compose.yml up -d` が成功する
- `docker compose -f infra/keycloak/docker-compose.yml ps` で PostgreSQL が `healthy`、Keycloak が起動状態である
- `http://localhost:8080` にアクセスして管理コンソールが表示され、初期管理者ユーザーでログインできる

------

## まとめ

今回のセットアップで、Docker を使って Keycloak と PostgreSQL をローカル環境に起動する流れを整理できた。  
今後はこの環境を利用して、Realm、Client、User の作成や認可設定の検証を進めていく予定である。
