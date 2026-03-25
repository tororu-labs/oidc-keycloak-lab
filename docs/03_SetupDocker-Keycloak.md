# Setup Docker Keycloak

## ここでのゴール

この手順では、Docker を使って Keycloak と PostgreSQL を起動し、次の状態に到達することをゴールとする。

- Docker Desktop を使える状態にする
- `infra/keycloak/.env` と `docker-compose.yml` を用意する
- Docker Compose で Keycloak と PostgreSQL を起動する
- Keycloak の管理コンソールへアクセスできる

必要な用語は [00_Glossary.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/00_Glossary.md) を参照する。

------

## この手順の流れ

この手順では、以下の流れで進める。

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

判定:

- `docker version` と `docker compose version` が表示される
- `docker run hello-world` が成功する

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

判定:

- `infra/keycloak/.env` を作成し、必要な環境変数を書ける

完了時の状態:

Keycloak と PostgreSQL が参照するデータベース名、接続ユーザー、初期管理者ユーザーの情報をローカルファイルで管理できる状態になった。

補足:

- `.env` には秘密情報が含まれるため、本番環境では環境変数やシークレット管理ツールを使う想定とする

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

判定:

- `docker compose` で Keycloak と PostgreSQL をまとめて起動できる設定ファイルを用意できる

完了時の状態:

`docker compose` で Keycloak と PostgreSQL をまとめて起動できる設定ファイルが用意できる。

補足:

- `postgres` サービスは `pgdata` volume を利用し、データベースの内容を永続化する構成にした。
- `keycloak` サービスは `depends_on` と PostgreSQL 側の `healthcheck` を利用し、DB の起動確認後に接続する構成にした。
- `127.0.0.1:8080:8080` を指定することで、Keycloak の管理画面をローカル PC からのみ参照できるようにした。
- `name: iam-lab-study-keycloak` を明示し、このプロジェクトで作られる container・network・volume の名前を判別しやすくした。

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

起動時の衝突や既存 resource の扱いについては `notes/02_Docker/MEMO_ComposeFileTroubleshooting.md`、
`up / down / down -v` の違いは `notes/02_Docker/01_ComposeLifecycle.md`、
デバッグ時の確認観点は `notes/02_Docker/02_DebugChecklist.md` に整理した。

判定:

`docker compose ps` で PostgreSQL コンテナが `healthy` となり、Keycloak コンテナが起動状態になっていれば、Compose による起動は成功と判断した。

補足:

- 起動方法や切り分けの共通整理は [01_LocalStartup.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/01_LocalStartup.md) と [03_Troubleshooting.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/03_Troubleshooting.md) を参照する

------

## 管理コンソールの確認

ブラウザで `http://localhost:8080` にアクセスし、Keycloak の管理コンソールが表示されることを確認した。

判定:

- Keycloak の管理コンソールが表示される
- `.env` に設定した初期管理者ユーザーでログインできる
- Keycloak をローカル環境から操作できる状態になっている

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

今回の手順で確認したこと:

- Docker Desktop を使える状態にした
- Keycloak 用 `.env` と `docker-compose.yml` を作成した
- PostgreSQL と Keycloak を起動した
- 管理コンソールへアクセスできることを確認した

ここまでで、ローカル環境で Keycloak を使った IAM 検証を始める土台を用意できた。  
次は [04_SetupKeycloak.md](/Users/tororu/workspace/labs/iam-lab-study/docs/04_SetupKeycloak.md) を参照し、realm、user、role、client を設定する。

------

## 関連ドキュメント

- [01_LocalStartup.md](./Reference/01_LocalStartup.md) を参照
- [03_Troubleshooting.md](./Reference/03_Troubleshooting.md) を参照
- [04_SetupKeycloak.md](./04_SetupKeycloak.md) を参照
