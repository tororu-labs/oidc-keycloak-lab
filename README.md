# iam-lab-study

IAM を学ぶための個人用ラボリポジトリです。  
OIDC、OAuth 2.0、Keycloak、セキュリティアーキテクチャを段階的に整理していく土台として使っています。  
現時点では Git / GitHub の理解メモ、Python 仮想環境の整備、Docker を使った Keycloak の初期導入までを進めており、検証用アプリや認証フローの実装はこれから追加する段階です。

## リポジトリ概要

このリポジトリは、IAM 関連技術を手を動かしながら学ぶための学習記録置き場です。

今は Git / GitHub、Python 開発環境、Keycloak のローカル起動環境を順番に整えながら、README を含むドキュメントを読み返せば状態を追える構成にしています。  
まだ実装中心のフェーズではなく、まずは学習と検証を始めるための土台を固めている段階です。

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
- Git の基本フロー、コミットメッセージ、状態遷移に関する学習メモ
- Docker Compose の見直しや衝突対応に関するメモ
- 個人用の作業メモ置き場としての `scratch/`

一方で、Realm / Client / User / Role の具体的な設定、OIDC / OAuth のフロー検証、検証用アプリの実装はまだこれからです。  
この README は、その途中状態を正確に表す中間版として記載しています。

## この repo の進め方

この repo では、実装や環境構築そのものだけでなく、その内容をあとから追える形で文書化することも進捗の一部として扱っています。

通常は、以下の流れで更新します。

1. 実装、設定変更、環境構築、動作確認を行う
2. 試行錯誤、判断理由、補足調査がある場合は必要に応じて `notes/` に残す
3. 内容が固まったら、再現したい手順や参照用の整った内容を `docs/` に記録する
4. 最後に `README.md` へ現在の進捗と主要ドキュメントを反映する

この役割分担により、`README.md` は入口と全体要約、`docs/` は再現しやすい手順書や参照用の整った文書、`notes/` は学習途中の記録や整理メモとして使い分ける。

## ディレクトリ構成

```text
iam-lab-study/
├── README.md
├── apps/
├── docs/
│   ├── 00_SetupDocker-Keycloak.md
│   ├── 00_SetupGitHubRepository.md
│   ├── 00_SetupVenv.md
│   └── _TEMPLATE.md
├── infra/
│   └── keycloak/
│       └── docker-compose.yml
├── notes/
│   ├── 01_Git/
│   └── 02_DockerKeycloak/
└── scratch/
```

- `docs/`: セットアップ手順や今後の構成資料を置くディレクトリ
- `apps/`: 検証用アプリを置く予定のディレクトリ。現時点ではプレースホルダ
- `infra/keycloak/`: Keycloak と PostgreSQL を Docker Compose で起動するための構成を置くディレクトリ
- `notes/01_Git/`: Git の基本操作やコミット運用に関する学習メモ
- `notes/02_DockerKeycloak/`: Docker Compose の見直しや衝突対応に関するメモ
- `scratch/`: 一時メモや作業途中の内容を置くローカル補助ディレクトリ

ローカル作業用として `.venv/`、`.vscode/`、`infra/keycloak/.env` も存在するが、上の構成図では主な内容だけを示している。

## 主要ドキュメント

- [docs/00_SetupGitHubRepository.md](docs/00_SetupGitHubRepository.md)  
  GitHub リポジトリ作成、SSH 鍵設定、ローカル clone、初期ディレクトリ作成までの記録
- [docs/00_SetupVenv.md](docs/00_SetupVenv.md)  
  Python 仮想環境 `.venv` と VSCode 設定の初期導入手順
- [docs/00_SetupDocker-Keycloak.md](docs/00_SetupDocker-Keycloak.md)  
  Docker Desktop、PostgreSQL、Keycloak の初期導入と起動確認の記録
- [notes/01_Git/01_GitBasicFlow.md](notes/01_Git/01_GitBasicFlow.md)  
  Git の基本的な作業フローを整理したメモ
- [notes/01_Git/02_GitCommitMessage.md](notes/01_Git/02_GitCommitMessage.md)  
  コミットメッセージの書き方をまとめたメモ
- [notes/01_Git/03_GitStateFlow.md](notes/01_Git/03_GitStateFlow.md)  
  作業ツリー、ステージング、ローカルブランチ、リモートの関係を整理したメモ
- [notes/02_DockerKeycloak/00_ComposeFile.md](notes/02_DockerKeycloak/00_ComposeFile.md)  
  Docker Compose の設定見直しと名前衝突対応のメモ

セットアップの詳細コマンドは README に再掲せず、上記の `docs/` 配下ドキュメントにまとめています。

## 現在の進捗

- GitHub 上のリポジトリ作成とローカル環境への clone を実施済み
- SSH 接続設定の手順を記録済み
- Python の `.venv` と VSCode 設定を整備済み
- `infra/keycloak/` に `.env` と `docker-compose.yml` を作成済み
- Docker で PostgreSQL と Keycloak を起動し、管理コンソールの表示確認まで実施済み
- Git の基本操作を理解するためのノートを作成済み
- 学習用のディレクトリ構成を作成済み
- Keycloak の初期導入は完了したが、認証・認可の実装検証は未着手

## 今後の予定

- `apps/` に認証・認可の検証用アプリを追加する
- Keycloak で Realm / Client / User / Role を作成し、設定手順を整理する
- OIDC / OAuth 2.0 のフローを実際に動かして検証する
- IAM / OIDC / OAuth 2.0 の学習メモを増やす
- 学習内容を README や関連ドキュメントへ継続的に反映する
