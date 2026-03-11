# venv環境のsetup

## 目的

- Python の仮想環境を作成するための `venv` をセットアップする手順を記録する
- これにより、プロジェクトごとに依存関係を管理し、環境の衝突を避けることができる。
- VSCode での Python 開発環境を整えるための基本的な手順も含む。
- このドキュメントは、IAM ラボのセットアップの一環として、Python を使用するプロジェクトで仮想環境を構築するためのガイドラインを提供することを目的とする。
  
## 事前準備

- Python がインストールされていることを確認する。
  - ターミナルで `python --version` または `python3 --version` を実行して、Python のバージョンを確認する。

## 仮想環境の作成

- プロジェクトのルートディレクトリに移動する。
  - 例: `cd ~/Projects/iam-lab-study`
- `venv` を使用して仮想環境を作成する。
  - コマンド: `python -m venv .venv`
  - これにより、プロジェクト内に `.venv` という名前の仮想環境が作成される。
- 仮想環境をアクティブにする。
  - macOS/Linux: `source .venv/bin/activate`
  - Windows: `.venv\Scripts\activate`
- 仮想環境がアクティブになっていることを確認する。
  - ターミナルのプロンプトに `(.venv)` が表示される。
  - `which python` または `where python` を実行して、仮想環境内の Python が使用されていることを確認する.  

~~~zsh
cd ~/Projects/iam-lab-study
python -m venv .venv
source .venv/bin/activate # 仮想環境のアクティベート
which python
~~~

## VSCodeでの設定

- VSCode を開き、プロジェクトのルートディレクトリをワークスペースとして開く。
- VSCode のコマンドパレットを開く（`Ctrl+Shift+P` または `Cmd+Shift+P`）。
- 「Python: Select Interpreter」を選択し、プロジェクトの `.venv` 内の Python インタープリターを選択する。
  - 今回は、`iam-lab-study/.venv/bin/python` を選択する。
- これにより、VSCode 内で Python コードを実行する際に、仮想環境が使用されるようになる。
- 必要に応じて、VSCode のターミナルも仮想環境を使用するように設定することができる。
- ターミナルで `python --version` を実行して、VSCode のターミナルが仮想環境を使用していることを確認する。
  - 今回は、`Python 3.12.12` が表示される。
- VSCode の設定ファイル（`settings.json`）に、仮想環境のパスを明示的に指定することもできる。
  - 例: `"python.pythonPath": "${workspaceFolder}/.venv/bin/python"`
  - これにより、VSCode が常にプロジェクトの仮想環境を使用するようになる。

### 補足

- 下記では、VSCode の設定ファイルを作成して、仮想環境のパスを指定する方法を示す。

~~~zsh
mkdir -p .vscode

cat > .vscode/settings.json <<'EOF'
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
EOF
~~~

## まとめ

初学者すぎて、まだ依存関係によるエラーに出会っておらず、仮想環境の重要性を実感できていないが、開発のお作法として作成しておく。

- 仮想環境を使用することで、プロジェクトごとに依存関係を管理し、環境の衝突を避けることができる。
