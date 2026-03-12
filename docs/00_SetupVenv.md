# Setup Python Virtual Environment (venv)

## 目的

このドキュメントは、IAM Study Lab の Python 開発環境を整えるために、`venv` を使った仮想環境の作成手順を記録するものである。  
主な目的は以下の通り。

- プロジェクトごとに独立した Python 仮想環境を作成する
- 依存関係の衝突を避けられるようにする
- VSCode で `.venv` を利用する設定を整える
- 今後の Python アプリ開発に再利用できる初期導入手順を残す

### 用語

- venv: Python 標準機能として提供されている仮想環境作成の仕組み
- 仮想環境: プロジェクトごとに独立した Python とパッケージ群を持つ実行環境
- activate: シェルが仮想環境内の Python を優先して使う状態に切り替えること
- interpreter: 実際に Python コードを実行する Python 本体
- `settings.json`: VSCode のワークスペース設定を記述するファイル

------

## 実施概要

今回のセットアップでは、以下の流れで作業を進めた。

1. `python3 --version` で Python が利用可能か確認
2. `python3 -m venv .venv` で仮想環境を作成
3. `source .venv/bin/activate` で仮想環境を有効化し、`which python` で確認
4. VSCode で `.venv` の Python インタープリターを選択
5. 必要に応じて `.vscode/settings.json` を作成して設定を固定

------

## Python の確認

まず、ローカル環境で Python 3 が利用できることを確認した。

~~~zsh
python3 --version
~~~

実施時点では、`Python 3.12.12` が表示された。

### 判定

`python3 --version` が成功し、Python 3 のバージョンが表示されたため、`venv` を使った仮想環境作成を進められると判断した。

------

## 仮想環境の作成

プロジェクトのルートディレクトリへ移動し、`.venv` という名前で仮想環境を作成した。

~~~zsh
cd ~/Projects/iam-lab-study
python3 -m venv .venv
~~~

### この時点の状態

プロジェクト直下に `.venv` ディレクトリが作成され、IAM Study Lab 専用の Python 実行環境が用意された。

------

## 仮想環境の有効化と確認

作成した仮想環境を有効化し、使用される Python が `.venv` 内のものに切り替わっていることを確認した。

~~~zsh
source .venv/bin/activate
which python
~~~

ターミナルのプロンプトに `(.venv)` が表示され、`which python` の結果が `.venv/bin/python` を指していれば、仮想環境が有効になっていると判断できる。

### 仮想環境有効化の判定

- プロンプトに `(.venv)` が表示される
- `which python` が `.venv/bin/python` を指している

------

## VSCode のインタープリター設定

VSCode を開き、プロジェクトの仮想環境を利用するようにインタープリターを設定した。

- プロジェクトのルートディレクトリをワークスペースとして開く
- コマンドパレットを開く
- `Python: Select Interpreter` を選択する
- `iam-lab-study/.venv/bin/python` を選択する

### インタープリター設定実施時の状態

VSCode 上で Python コードを実行するときに、プロジェクト専用の `.venv` が利用される状態になった。

------

## `settings.json` の作成

VSCode の設定をワークスペースに固定したい場合は、`.vscode/settings.json` を作成して仮想環境のパスを明示できる。

~~~zsh
mkdir -p .vscode

cat > .vscode/settings.json <<'EOF'
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
EOF
~~~

### 補足

- `python.defaultInterpreterPath` は、VSCode が既定で使う Python を `.venv` に固定するための設定である。
- `python.terminal.activateEnvironment` は、VSCode 内のターミナル起動時に仮想環境を有効化しやすくするための設定である。

### `settings.json` の作成後の状態

VSCode を開いたときに、ワークスペース単位で `.venv` を優先利用しやすい設定がそろった。

------

## 本ドキュメントで完了したこと

以下が完了した状態になった。

- Python 3 の利用確認
- `.venv` の作成
- 仮想環境の有効化確認
- VSCode のインタープリター設定
- ワークスペース設定ファイルの作成

つまり、IAM Study Lab で Python アプリを作り始めるための基本的な実行環境が整った。

------

## 実行コマンド一覧

### Python / venv 関連

~~~zsh
python3 --version # Python 3 の利用確認
cd ~/Projects/iam-lab-study # プロジェクトルートへ移動
python3 -m venv .venv # 仮想環境の作成
source .venv/bin/activate # 仮想環境の有効化
which python # 使用中の Python 確認
~~~

### VSCode 設定ファイル関連

~~~zsh
mkdir -p .vscode # VSCode 設定ディレクトリの作成
~~~

------

## 完了判定

以下を満たしたため、`venv` を使った Python 開発環境の初期導入は完了とする。

- `python3 --version` が成功する
- `.venv` ディレクトリが作成されている
- `source .venv/bin/activate` 後にプロンプトへ `(.venv)` が表示される
- `which python` が `.venv/bin/python` を指している
- VSCode で `.venv` のインタープリターが選択されている
- `.vscode/settings.json` を作成した場合、`.venv` を参照する設定が記述されている

------

## まとめ

今回のセットアップで、IAM Study Lab の Python 開発で利用する仮想環境を作成し、VSCode から利用するための基本設定まで整理できた。  
今後はこの `.venv` を使って必要なパッケージを追加し、FastAPI などの検証アプリを進めていく予定である。
