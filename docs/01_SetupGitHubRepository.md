# Setup GitHub Repository

## ここでのゴール

この手順では、Git / GitHub の初期導入を行い、次の状態に到達することをゴールとする。

- GitHub 上に IAM ラボ用のリポジトリを作成する
- ローカル Mac から GitHub へ SSH 接続できるようにする
- ローカルにリポジトリを clone し、初期ディレクトリ構成を作成する
- 初回 commit / push まで完了する

必要な用語は [00_Glossary.md](Reference/00_Glossary.md) を参照する。

------

## この手順の流れ

この手順では、以下の流れで進める。

1. GitHub 上で IAM ラボ用リポジトリを作成
2. GitHub 用の SSH 鍵を作成
3. 公開鍵を GitHub に登録
4. `ssh -T git@github.com` で SSH 接続確認
5. ローカルにリポジトリを clone
6. 初期ディレクトリを作成
7. 初回 commit / push を実施

------

## GitHub リポジトリ作成（GitHubのWeb側で作業）

- Repository name: `oidc-keycloak-lab`
- Visibility: `Public`
- README: 作成
- `.gitignore`: 作成
- License: MIT License

判定:

- GitHub 上にリポジトリが作成されている
- `README.md`、`.gitignore`、`LICENSE` を含む初回コミットが存在している

------

## SSH 接続設定

GitHub へローカル環境から安全に push / pull するため、HTTPS ではなく SSH 接続を利用することにした。  
SSH 接続では、ローカルに秘密鍵を保持し、GitHub に公開鍵を登録することで認証を行う。

------

## SSH 鍵の確認

既存の SSH 鍵があるかを確認した。

~~~zsh
ls -al ~/.ssh
~~~

この時点では、SSH 鍵は存在しない状態だったため、新たに作成することにした。

判定:

- 既存鍵の有無を確認できる

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

判定:

- `~/.ssh/` に GitHub 用の鍵を作成できる

------

## ssh-agent の起動と鍵の追加

コマンドで ssh-agent を起動し、作成した秘密鍵をキーチェーンに追加した。

~~~zsh
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
~~~

補足:

- macOS 以外の環境では、以下のコマンドで鍵を追加することもある

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

判定:

- 公開鍵を GitHub へ登録できる状態になっている

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

判定:

- 上記メッセージが表示され、SSH 認証が完了している

------

## ローカルへのリポジトリ clone

~~~zsh
mkdir -p ~/projects
cd ~/projects
~~~

~~~zsh
git clone git@github.com:tororu-labs/oidc-keycloak-lab.git
cd oidc-keycloak-lab
~~~

~~~zsh
pwd
git remote -v
git branch
ls -la
~~~

判定:

- ローカルにリポジトリを clone できる
- `git remote -v` で GitHub への接続先を確認できる
- 作業ディレクトリが用意できる

------

## 初期ディレクトリ構成の作成

IAM ラボの用途ごとにディレクトリを分けるため、以下を作成した。

~~~zsh
mkdir -p docs apps infra
touch docs/.gitkeep apps/.gitkeep infra/.gitkeep
~~~

補足:

- `.gitkeep` は、Git が空のディレクトリを管理できないため、空のフォルダを残すために置いている

~~~text
oidc-keycloak-lab/
├── README.md
├── .gitignore
├── docs/
├── apps/
└── infra/
~~~

判定:

- 必要な初期ディレクトリを作成できる

補足:

- `docs/`
  - Setup と Reference を置く
- `apps/`
  - FastAPI などの検証アプリ
- `infra/`
  - Keycloak、DB、Docker Compose などの構成ファイル

------

## Git 状態確認

~~~zsh
git status
~~~

この時点では、新しく作成したディレクトリ群が `Untracked files` として表示された。
この確認のタイミングで、意図しないファイルが混ざっていないかも合わせて見た。

判定:

- 意図したファイルだけが追加対象になっていることを確認できる

------

## 初回 commit / push

~~~zsh
git add .
~~~

今回は `git add .` を使ったが、実行前に `git status` で対象を確認してから進めた。

~~~zsh
git commit -m "chore: initialize local IAM lab structure"
~~~

~~~zsh
git push origin main
~~~

判定:

- ローカルに初期構成を commit した
- GitHub 上の `main` ブランチへ push した
- GitHub とローカルの同期が取れた

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
git clone git@github.com:tororu-labs/oidc-keycloak-lab.git #リポジトリをローカルに clone
cd oidc-keycloak-lab #リポジトリディレクトリに移動

mkdir -p docs apps infra #初期ディレクトリ構成の作成
touch docs/.gitkeep apps/.gitkeep infra/.gitkeep #用途ごとのディレクトリの作成

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

今回の手順で確認したこと:

- GitHub リポジトリを作成した
- SSH 接続を設定した
- ローカルへ clone し、初期ディレクトリ構成を作成した
- 初回 commit / push を完了した

ここまでで、IAM Study Lab の開発と学習を始めるための Git / GitHub 環境を用意できた。  
次は [02_SetupVenv.md](02_SetupVenv.md) を参照し、Python の実行環境を整える。

------

## 関連ドキュメント

- [02_SetupVenv.md](./02_SetupVenv.md) を参照
