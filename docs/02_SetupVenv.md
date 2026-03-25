# Setup Python Virtual Environment (venv)

## ここでのゴール

この手順では、Python の仮想環境を作成し、次の状態に到達することをゴールとする。

- プロジェクト専用の `.venv` を作成する
- 仮想環境を有効化できる
- VSCode で `.venv` を使う設定を整える

必要な用語は [00_Glossary.md](/Users/tororu/workspace/labs/iam-lab-study/docs/Reference/00_Glossary.md) を参照する。

------

## この手順の流れ

この手順では、以下の流れで進める。

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

判定:

- `python3 --version` が成功し、Python 3 のバージョンが表示される

------

## 仮想環境の作成

プロジェクトのルートディレクトリへ移動し、`.venv` という名前で仮想環境を作成した。

~~~zsh
cd ~/workspace/labs/iam-lab-study
python3 -m venv .venv
~~~

判定:

- プロジェクト直下に `.venv` ディレクトリを作成できる

完了時の状態:

プロジェクト専用の Python 実行環境が用意される。

------

## 仮想環境の有効化と確認

作成した仮想環境を有効化し、使用される Python が `.venv` 内のものに切り替わっていることを確認した。

~~~zsh
source .venv/bin/activate
which python
~~~

ターミナルのプロンプトに `(.venv)` が表示され、`which python` の結果が `.venv/bin/python` を指していれば、仮想環境が有効になっていると判断できる。

仮想環境の有効化はターミナルごとに独立している。新しいターミナルを開いた場合や、VSCode 上でコマンドを 1 行だけ単独実行した場合は、実行前に再度 `which python` を確認する。

判定:

- プロンプトに `(.venv)` が表示される
- `which python` が `.venv/bin/python` を指している

補足:

- 新しいターミナルを開いた場合や VSCode 上で単独実行した場合は、実行前に再度 `which python` を確認する

------

## VSCode のインタープリター設定

VSCode を開き、プロジェクトの仮想環境を利用するようにインタープリターを設定した。

- プロジェクトのルートディレクトリをワークスペースとして開く
- コマンドパレットを開く
- `Python: Select Interpreter` を選択する
- `iam-lab-study/.venv/bin/python` を選択する

判定:

- VSCode で `iam-lab-study/.venv/bin/python` を選択できる

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

判定:

- `.vscode/settings.json` を作成し、`.venv` を参照する設定を書ける

補足:

- `python.defaultInterpreterPath` は、VSCode が既定で使う Python を `.venv` に固定するための設定である。
- `python.terminal.activateEnvironment` は、VSCode 内のターミナル起動時に仮想環境を有効化しやすくするための設定である。
- すべての実行方法で `.venv` が必ず使われるわけではない。パッケージ導入時は `which python` を確認するか、`./.venv/bin/python -m pip ...` のように `.venv` の Python を明示すると確実である。

------

## 実行コマンド一覧

### Python / venv 関連

~~~zsh
python3 --version # Python 3 の利用確認
cd ~/workspace/labs/iam-lab-study # プロジェクトルートへ移動
python3 -m venv .venv # 仮想環境の作成
source .venv/bin/activate # 仮想環境の有効化
which python # 使用中の Python 確認
./.venv/bin/python -m pip --version # .venv の pip を明示して確認
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

今回の手順で確認したこと:

- Python 3 が利用できることを確認した
- `.venv` を作成し、有効化できることを確認した
- VSCode で `.venv` を使う設定を整えた

ここまでで、IAM Study Lab の Python 実行環境を用意できた。  
次は [03_SetupDocker-Keycloak.md](/Users/tororu/workspace/labs/iam-lab-study/docs/03_SetupDocker-Keycloak.md) を参照し、Keycloak のローカル起動環境を整える。

------

## 関連ドキュメント

- [03_SetupDocker-Keycloak.md](./03_SetupDocker-Keycloak.md) を参照
