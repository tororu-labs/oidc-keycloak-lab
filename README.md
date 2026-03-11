# iam-lab-study

IAM を学ぶための個人用ラボリポジトリです。  
OIDC、OAuth 2.0、Keycloak、セキュリティアーキテクチャを段階的に整理していく土台として使っています。  
現時点では Git / GitHub の理解メモとリポジトリ整備が主内容で、実装や検証用の `apps/` `infra/` はこれから追加する段階です。

## リポジトリ概要

このリポジトリは、IAM 関連技術を手を動かしながら学ぶための学習記録置き場です。

今は環境準備と Git / GitHub の基礎整理を進めており、README を含むドキュメントを読みながら状態を追える構成にしています。  
実行手順や Quick Start をまとめる段階ではなく、まずは学習の土台と記録を整えているフェーズです。

## 学習テーマ

- IAM の基礎理解
- OIDC / OAuth 2.0 の整理
- Keycloak を使った認証・認可の検証
- セキュリティアーキテクチャの学習
- 学習を継続するための Git / GitHub 運用の整理

## 現在この repo に入っているもの

- GitHub リポジトリ作成、SSH 接続設定、ローカル clone までのセットアップ記録
- Git の基本フロー、コミットメッセージ、状態遷移に関する学習メモ
- 今後 `apps/` や `infra/` を追加するためのディレクトリ構成
- 個人用の作業メモ置き場としての `scratch/`

一方で、Keycloak / OAuth / OIDC の実装、検証用アプリ、Docker 構成はまだ未追加です。  
この README は、その途中状態を正確に表す中間版として記載しています。

## ディレクトリ構成

```text
iam-lab-study/
├── README.md
├── apps/
├── docs/
├── infra/
├── notes/
└── scratch/
```

- `docs/`: セットアップ手順や今後の構成資料を置くディレクトリ
- `notes/`: 学習メモ、概念整理、理解補助のノート
- `apps/`: 検証用アプリを置く予定のディレクトリ。現時点ではプレースホルダ
- `infra/`: Keycloak や関連構成を置く予定のディレクトリ。現時点ではプレースホルダ
- `scratch/`: 一時メモや作業途中の内容を置く補助ディレクトリ

## 主要ドキュメント

- [docs/00_SetupGitHubRepository.md](docs/00_SetupGitHubRepository.md)  
  GitHub リポジトリ作成、SSH 鍵設定、ローカル clone、初期ディレクトリ作成までの記録
- [notes/01_Git/01_GitBasicFlow.md](notes/01_Git/01_GitBasicFlow.md)  
  Git の基本的な作業フローを整理したメモ
- [notes/01_Git/02_GitCommitMessage.md](notes/01_Git/02_GitCommitMessage.md)  
  コミットメッセージの書き方をまとめたメモ
- [notes/01_Git/03_GitStateFlow.md](notes/01_Git/03_GitStateFlow.md)  
  作業ツリー、ステージング、ローカルブランチ、リモートの関係を整理したメモ

セットアップの詳細コマンドは README に再掲せず、上記の `docs/` 配下ドキュメントにまとめています。

## 現在の進捗

- GitHub 上のリポジトリ作成とローカル環境への clone を実施済み
- SSH 接続設定の手順を記録済み
- Git の基本操作を理解するためのノートを作成済み
- 学習用のディレクトリ構成を作成済み
- IAM / OIDC / OAuth / Keycloak の実装検証は未着手

## 今後の予定

- `infra/` に Keycloak や関連構成を追加する
- `apps/` に認証・認可の検証用アプリを追加する
- IAM / OIDC / OAuth 2.0 の学習メモを増やす
- 学習内容を README や関連ドキュメントへ継続的に反映する
