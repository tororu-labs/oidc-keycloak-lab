# 00_Setup GitHub Repository

## 目的

このドキュメントは、IAM Study Lab を始めるにあたって実施した Git / GitHub の初期導入手順を記録するものである。  
主な目的は以下の通り。

- GitHub 上に IAM ラボ用のリポジトリを作成する
- ローカル Mac から GitHub へ SSH 接続できるようにする
- ローカルにリポジトリを clone し、初期ディレクトリ構成を作成する
- 初回 commit / push までの流れを残す

### 用語

- commit:変更内容をローカルリポジトリに保存すること
- push:ローカルリポジトリの変更をGitHubなどのリモートリポジトリに反映させること
- リモートリポジトリ:GitHubなどのオンライン上に存在するリポジトリのこと
- ローカルリポジトリ:開発者のPCなどのローカル環境に存在するリポジトリのこと
- clone: GitHub 上のリポジトリをローカルにコピーすること
- Ed25519形式: SSH 鍵の形式の一つで、セキュリティが高く推奨されている
- ステージング: commit する前に変更内容を一時的に保存すること。`git add` コマンドで行う

------

## 実施概要

今回のセットアップでは、以下の流れで作業を進めた。

1. GitHub 上で IAM ラボ用リポジトリを作成
2. GitHub 用の SSH 鍵を作成
3. 公開鍵を GitHub に登録
4. `ssh -T git@github.com` で SSH 接続確認
5. ローカルにリポジトリを clone
6. 初期ディレクトリを作成
7. 初回 commit / push を実施

------

## GitHub リポジトリ作成（GitHubのWeb側で作業）

### 作成したリポジトリ

- Repository name: `iam-lab-study`
- Visibility: `Private`

### 初期設定

- README: 作成
- `.gitignore`: 作成
- License: 追加しない

### この時点の状態

GitHub 上に空のリポジトリができ、`README.md` と `.gitignore` を含む初回コミットが存在する状態になった。

------

## SSH 接続設定

### 背景

GitHub へローカル環境から安全に push / pull するため、HTTPS ではなく SSH 接続を利用することにした。  
SSH 接続では、ローカルに秘密鍵を保持し、GitHub に公開鍵を登録することで認証を行う。

------

## SSH 鍵の確認

既存の SSH 鍵があるかを確認した。

~~~zsh
ls -al ~/.ssh
~~~

この時点では、SSH 鍵は存在しない状態だったため、新たに作成することにした。

------

## SSH 鍵の作成

Ed25519 形式で GitHub 用の SSH 鍵を作成した。

~~~zsh
ssh-keygen -t ed25519 -C "your_email@example.com"
~~~

入力時の方針:

- 保存先: デフォルトを利用
- パスフレーズ: 設定（セキュリティ向上のため）
- 確認のため再入力

------

## ssh-agent の起動と鍵の追加

コマンドで ssh-agent を起動し、作成した秘密鍵をキーチェーンに追加した。

~~~zsh
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
~~~

- 補足:macOS 以外の環境では、以下のコマンドで鍵を追加することもある。

~~~bash
ssh-add ~/.ssh/id_ed25519
~~~

------

## 公開鍵のコピー

GitHub に登録するため、公開鍵をクリップボードへコピーした。

~~~zsh
pbcopy < ~/.ssh/id_ed25519.pub
~~~

必要に応じて内容確認:

~~~zsh
cat ~/.ssh/id_ed25519.pub
~~~

------

## GitHub への公開鍵登録（GitHubのWeb側で作業）

GitHub の以下画面から公開鍵を登録した。

- Settings
- SSH and GPG keys
- New SSH key

設定内容:

- Title: 使用端末を識別できる名前など（例: `MacBook Pro 2020`）
- Key type: `Authentication Key`
- Key: `id_ed25519.pub` の内容をそのままペースト
- `id_ed25519.pub`は`ssh-ed25519 AAAA... your_email@example.com`の形になる

------

## SSH 接続確認

以下コマンドで GitHub への SSH 接続を確認した。

~~~zsh
ssh -T git@github.com
~~~

初回接続時にはホスト確認が表示されることがあるため、内容を確認して `yes` を入力した。
`Are you sure you want to continue connecting (yes/no/[fingerprint])?`

正常時の例:

~~~text
Hi tororu-labs! You've successfully authenticated, but GitHub does not provide shell access.
~~~

### 判定

このメッセージが表示されたため、SSH 認証は正常に完了していると判断した。

------

## ローカルへのリポジトリ clone

### 作業用ディレクトリ作成

~~~zsh
mkdir -p ~/projects
cd ~/projects
~~~

### clone 実行

~~~zsh
git clone git@github.com:tororu-labs/iam-lab-study.git
cd iam-lab-study
~~~

### 確認

~~~zsh
pwd
git remote -v
git branch
ls -la
~~~

ここでは、現在の作業ディレクトリ、リモート接続先、ブランチも合わせて確認した。

この時点で、GitHub リポジトリと接続されたローカル作業ディレクトリができた。

------

## 初期ディレクトリ構成の作成

IAM ラボの用途ごとにディレクトリを分けるため、以下を作成した。

~~~zsh
mkdir -p docs notes apps infra scratch
touch docs/.gitkeep notes/.gitkeep apps/.gitkeep infra/.gitkeep scratch/.gitkeep
~~~

- 補足: `.gitkeep` ファイルは、Git が空のディレクトリを管理できないため、空のフォルダを残すために置いている。

### 作成した構成

~~~text
iam-lab-study/
├── README.md
├── .gitignore
├── docs/
├── notes/
├── apps/
├── infra/
└── scratch/
~~~

### 各ディレクトリの用途

- `docs/`
  - 設計資料、構成図、手順書、runbook
- `notes/`
  - 学習メモ、理解メモ、調査メモ
- `apps/`
  - FastAPI などの検証アプリ
- `infra/`
  - Keycloak、DB、Docker Compose などの構成ファイル
- `scratch/`
  - 一時作業用の置き場
  - commit 前に中身を確認し、残したいものだけを管理する想定

------

## Git 状態確認

~~~zsh
git status
~~~

この時点では、新しく作成したディレクトリ群が `Untracked files` として表示された。
この確認のタイミングで、意図しないファイルが混ざっていないかも合わせて見た。

------

## 初回 commit / push

### add

~~~zsh
git add .
~~~

今回は `git add .` を使ったが、実行前に `git status` で対象を確認してから進めた。

### commit

~~~zsh
git commit -m "chore: initialize local IAM lab structure"
~~~

### push

~~~zsh
git push origin main
~~~

### 実行結果の意味

- ローカルに初期構成を commit した
- GitHub 上の `main` ブランチへ push した
- GitHub とローカルの同期が取れた

------

## この時点で完了したこと

以下が完了した状態になった。

- GitHub リポジトリ作成
- SSH 接続設定
- ローカル clone
- 初期ディレクトリ構成作成
- 初回 commit / push

つまり、IAM Study Lab の開発・学習を始めるための土台ができた。

------

## 実行コマンド一覧

### SSH 設定関連

~~~zsh
ls -al ~/.ssh #SSH 鍵の確認
ssh-keygen -t ed25519 -C "your_email@example.com" #SSH 鍵の作成
eval "$(ssh-agent -s)" #ssh-agent の起動
ssh-add --apple-use-keychain ~/.ssh/id_ed25519 #秘密鍵をキーチェーンに追加
pbcopy < ~/.ssh/id_ed25519.pub #公開鍵をクリップボードにコピー
ssh -T git@github.com #SSH 接続確認
~~~

### リポジトリ取得と初期構成

~~~zsh
mkdir -p ~/projects #作業用ディレクトリ作成
cd ~/projects #作業ディレクトリに移動
git clone git@github.com:tororu-labs/iam-lab-study.git #リポジトリをローカルに clone
cd iam-lab-study #リポジトリディレクトリに移動

mkdir -p docs notes apps infra scratch #初期ディレクトリ構成の作成
touch docs/.gitkeep notes/.gitkeep apps/.gitkeep infra/.gitkeep scratch/.gitkeep #用途ごとのディレクトリの作成

git status #状態確認
git add . #変更をステージング（実行前に git status で対象を確認）
git commit -m "chore: initialize local IAM lab structure" #変更をコミット
git push origin main #変更をリモートに push
~~~

------

## 完了判定

以下を満たしたため、Git 導入は完了とする。

- `ssh -T git@github.com` が成功
- `git clone` が成功
- 初期ディレクトリ作成が成功
- `git push origin main` が成功

------

## まとめ

今回のセットアップで、IAM Study Lab の開発を始めるための Git / GitHub 環境が整った。
今後はこの環境を活用して、学習内容の記録やコードの管理を行っていく予定である。
