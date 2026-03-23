# iam-lab-study

IAM を学ぶための個人用ラボリポジトリです。  
OIDC、OAuth 2.0、Keycloak、セキュリティアーキテクチャを段階的に整理していく土台として使っています。  
現時点では Git / GitHub の理解メモ、Python 仮想環境の整備、Docker を使った Keycloak の初期導入、Keycloak GUI の基本設定、FastAPI を使った最小 OIDC ログイン検証、FastAPI 同士の BFF / Backend API 分離までを進めています。

## リポジトリ概要

このリポジトリは、IAM 関連技術を手を動かしながら学ぶための学習記録置き場です。

今は Git / GitHub、Python 開発環境、Keycloak のローカル起動環境を順番に整えながら、README を含むドキュメントを読み返せば状態を追える構成にしています。  
FastAPI ベースでの OIDC ログインと BFF / Backend API の最小分離までは進めており、次は Next.js を足して SPA / BFF 構成へ広げる段階です。

## 学習テーマ

- IAM の基礎理解
- OIDC / OAuth 2.0 の整理
- Keycloak を使った認証・認可の検証
- セキュリティアーキテクチャの学習
- 学習を継続するための Git / GitHub 運用の整理

## 現在この repo に入っているもの

- GitHub リポジトリ作成、SSH 接続設定、ローカル clone までのセットアップ記録
- Python の `venv` と VSCode 設定に関するセットアップ記録
- Docker Compose を使って Keycloak と PostgreSQL を起動するための構成
- Keycloak GUI で `realm / user / role / client` を作成し、token 差分を確認する手順
- OIDC 一般論と Keycloak 固有の概念を分けて整理する学習メモ
- FastAPI を使って Keycloak の OIDC ログインを試す最小検証アプリ
- FastAPI の BFF から別 FastAPI API へ Access Token を渡し、JWT 検証付きで保護する最小検証アプリ
- 手順書どおりの実施内容をターミナルログとして残すための `scripts/doclog.zsh`
- Git の基本フロー、コミットメッセージ、状態遷移に関する学習メモ
- Docker Compose、Keycloak、OIDC の学習メモ
- 個人用の作業メモ置き場としての `scratch/`

一方で、Next.js 連携や audience 検証、より実務寄りの token / session 保持方式はまだこれからです。
この README は、その途中状態を表す中間版として記載しています。

## この repo の進め方

この repo では、実装や環境構築そのものだけでなく、その内容をあとから追える形で文書化することも進捗の一部として扱っています。

通常は、以下の流れで更新します。

1. 実装、設定変更、環境構築、動作確認を行う
2. 試行錯誤、判断理由、補足調査がある場合は必要に応じて `notes/` に残す
3. 内容が固まったら、再現したい手順や参照用の整った内容を `docs/` に記録する
4. 最後に `README.md` へ現在の進捗と主要ドキュメントを反映する

この役割分担により、`README.md` は入口と全体要約、`docs/` は再現しやすい手順書や参照用の整った文書、`notes/` は学習途中の記録や整理メモとして使い分ける。

## 手順ログの残し方

詳しい使い方は [`scratch/logs/手順ログの残し方.md`](scratch/logs/手順ログの残し方.md) に切り出した。
`doclog` の基本運用や注意点をまとめてあるので、必要なときはそちらを参照する。

## ディレクトリ構成

```text
iam-lab-study/
├── README.md
├── apps/
│   ├── demo_api/
│   │   ├── .env.example
│   │   ├── main.py
│   │   └── requirements.txt
│   └── demo_bff/
│       ├── .env.example
│       ├── main.py
│       └── requirements.txt
├── docs/
│   ├── 01_SetupGitHubRepository.md
│   ├── 02_SetupVenv.md
│   ├── 03_SetupDocker-Keycloak.md
│   ├── 04_SetupKeycloak.md
│   ├── 05_SetupFastAPI-OIDCLogin.md
│   ├── 06_SetupFastAPI-BackendAPI.md
│   └── _TEMPLATE.md
├── infra/
│   └── keycloak/
│       └── docker-compose.yml
├── notes/
│   ├── 01_Git/
│   ├── 02_Docker/
│   ├── 03_Keycloak/
│   └── 04_OIDC/
├── scripts/
│   └── doclog.zsh
└── scratch/
```

- `apps/`: 検証用アプリを置くディレクトリ。現時点では FastAPI による BFF と Backend API の最小検証アプリを配置
- `docs/`: セットアップ手順や今後の構成資料を置くディレクトリ
- `infra/keycloak/`: Keycloak と PostgreSQL を Docker Compose で起動するための構成を置くディレクトリ
- `notes/01_Git/`: Git の基本操作やコミット運用に関する学習メモ
- `notes/02_Docker/`: Docker Compose の見直しやライフサイクルに関するメモ
- `notes/03_Keycloak/`: Keycloak の realm / client / role / token 出力に寄った学習メモ
- `notes/04_OIDC/`: OIDC / OAuth 2.0 の一般概念に寄った学習メモ
- `scripts/`: 手順書実施時のログ取得を補助するスクリプトを置くディレクトリ
- `scratch/`: 一時メモや作業途中の内容を置くローカル補助ディレクトリ

ローカル作業用として `.venv/`、`.vscode/`、`infra/keycloak/.env` も存在するが、上の構成図では主な内容だけを示している。

## 主要ドキュメント

- [docs/01_SetupGitHubRepository.md](docs/01_SetupGitHubRepository.md)  
  GitHub リポジトリ作成、SSH 鍵設定、ローカル clone、初期ディレクトリ作成までの記録
- [docs/02_SetupVenv.md](docs/02_SetupVenv.md)  
  Python 仮想環境 `.venv` と VSCode 設定の初期導入手順
- [docs/03_SetupDocker-Keycloak.md](docs/03_SetupDocker-Keycloak.md)  
  Docker Desktop、PostgreSQL、Keycloak の初期導入と起動確認の記録
- [docs/04_SetupKeycloak.md](docs/04_SetupKeycloak.md)  
  Keycloak GUI で `realm / role / user / client` を作成し、token 差分を確認する手順
- [docs/05_SetupFastAPI-OIDCLogin.md](docs/05_SetupFastAPI-OIDCLogin.md)  
  FastAPI を使って Keycloak の OIDC ログインを実アプリから試す最小ハンズオン
- [docs/06_SetupFastAPI-BackendAPI.md](docs/06_SetupFastAPI-BackendAPI.md)
  FastAPI の BFF から別 FastAPI API へ Access Token を渡し、JWT 検証付き API 保護を確認するハンズオン
- [notes/01_Git/01_GitBasicFlow.md](notes/01_Git/01_GitBasicFlow.md)  
  Git の基本的な作業フローを整理したメモ
- [notes/01_Git/02_GitCommitMessage.md](notes/01_Git/02_GitCommitMessage.md)  
  コミットメッセージの書き方をまとめたメモ
- [notes/01_Git/03_GitStateFlow.md](notes/01_Git/03_GitStateFlow.md)  
  作業ツリー、ステージング、ローカルブランチ、リモートの関係を整理したメモ
- [notes/02_Docker/01_ComposeLifecycle.md](notes/02_Docker/01_ComposeLifecycle.md)
  Docker Compose の `up / stop / start / down / down -v` を整理したメモ
- [notes/02_Docker/02_DebugChecklist.md](notes/02_Docker/02_DebugChecklist.md)
  Docker / Compose / Keycloak 起動不良の切り分け観点を整理したメモ
- [notes/02_Docker/03_RecreateReset.md](notes/02_Docker/03_RecreateReset.md)
  再起動、再作成、初期化の判断を整理したメモ
- [notes/02_Docker/04_PortsEnvVolumes.md](notes/02_Docker/04_PortsEnvVolumes.md)
  ports、`.env`、volume の考え方を整理したメモ
- [notes/02_Docker/MEMO_ComposeFileTroubleshooting.md](notes/02_Docker/MEMO_ComposeFileTroubleshooting.md)  
  Docker Compose の設定見直しと名前衝突対応のメモ
- [notes/03_Keycloak/01_RealmClientRoleScope.md](notes/03_Keycloak/01_RealmClientRoleScope.md)
  Keycloak の `realm / client / role / client scope` の関係を整理したメモ
- [notes/03_Keycloak/02_ClientScopeMapper.md](notes/03_Keycloak/02_ClientScopeMapper.md)
  Keycloak の `client scope` と `mapper` が token 出力にどう効くかを整理したメモ
- [notes/03_Keycloak/03_KeycloakTroubleshooting.md](notes/03_Keycloak/03_KeycloakTroubleshooting.md)
  Keycloak GUI 設定で詰まりやすいポイントを整理したメモ
- [notes/03_Keycloak/MEMO_CompareTokensUsers.md](notes/03_Keycloak/MEMO_CompareTokensUsers.md)  
  `alice` と `bob` の token 比較メモ
- [notes/04_OIDC/01_AuthorizationCodeFlow.md](notes/04_OIDC/01_AuthorizationCodeFlow.md)
  Authorization Code Flow の全体像を整理したメモ
- [notes/04_OIDC/02_TokenKindsAndClaims.md](notes/04_OIDC/02_TokenKindsAndClaims.md)
  ID token / access token / refresh token と claim を整理したメモ
- [notes/04_OIDC/03_RedirectUriStateNonce.md](notes/04_OIDC/03_RedirectUriStateNonce.md)
  `redirect_uri`、`state`、`nonce` の役割を整理したメモ
- [notes/04_OIDC/04_PKCEAndConfidentialClient.md](notes/04_OIDC/04_PKCEAndConfidentialClient.md)
  PKCE と public / confidential client の違いを整理したメモ

セットアップの詳細コマンドは README に再掲せず、上記の `docs/` 配下ドキュメントにまとめています。

## 現在の進捗

- GitHub 上のリポジトリ作成とローカル環境への clone を実施済み
- SSH 接続設定の手順を記録済み
- Python の `.venv` と VSCode 設定を整備済み
- `infra/keycloak/` に `.env` と `docker-compose.yml` を作成済み
- Docker で PostgreSQL と Keycloak を起動し、管理コンソールの表示確認まで実施済み
- Keycloak の GUI で `lab` realm、`alice / bob`、`viewer / admin`、`demo-web` を作成済み
- `alice` と `bob` の token 差分を確認済み
- Keycloak 固有概念と OIDC 一般概念を分けたノートを追加済み
- `apps/demo_bff/` に FastAPI ベースの最小 OIDC ログイン検証アプリを追加済み
- `apps/demo_api/` に JWT 検証付き Backend API を追加済み
- Git の基本操作を理解するためのノートを作成済み
- 学習用のディレクトリ構成を作成済み
- FastAPI ベースでの BFF / Backend API 分離と JWT 検証は進めたが、Next.js 連携と audience 検証は未着手

## 今後の予定

- Next.js を追加し、SPA / BFF 構成へ段階的に進める
- Backend API 側に audience 検証や失敗系ハンズオンを追加する
- IAM / OIDC / OAuth 2.0 の学習メモを増やす
- 学習内容を README や関連ドキュメントへ継続的に反映する
