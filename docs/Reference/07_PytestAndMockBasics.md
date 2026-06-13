# 07 Pytest And Mock Basics

## 目的

このドキュメントは、`docs/10_SetupJWTEdgeCaseTests.md` を読む前の前提知識を整理するものである。

- pytest とは何か、なぜ使うのか
- fixture とは何か、どう使うのか
- patch（モック）とは何か、なぜ必要なのか
- 非同期テストとは何か

各概念の深い仕組みまでは追わない。「使い方を知る」ことがゴールである。

------

## pytest とは

pytest は「Python のコードが期待どおりに動くかを自動で確認するツール」である。

ブラウザで動作確認する場合、毎回ログインして画面を操作しなければならない。pytest を使うと、その確認をコマンド 1 つで自動化できる。特に「署名改ざんされた JWT を渡したとき 401 が返るか」のような異常系は、ブラウザでは再現しにくいが pytest なら再現できる。

~~~zsh
cd apps/demo_api
pytest tests/ -v
~~~

を実行すると、`tests/` 以下のファイルにある `test_` で始まる関数を順番に実行し、結果を一覧表示する。

~~~
PASSED tests/test_auth.py::test_valid_token
PASSED tests/test_auth.py::test_expired_token
FAILED tests/test_auth.py::test_wrong_audience
~~~

`PASSED` は期待どおり動いた、`FAILED` は期待と異なる結果が出た、を意味する。

------

## fixture とは

`@pytest.fixture` を付けた関数は fixture になる。fixture は「テスト用の準備物をまとめて使い回す仕組み」である。

たとえばテスト用の RSA 鍵を毎回生成すると時間がかかる。fixture にまとめることで、複数のテストが同じ鍵を使い回せる。

~~~python
@pytest.fixture(scope="session")
def rsa_key():
    return RSAKey.generate_key(2048, {"kid": "test-kid-1"}, private=True)
~~~

テスト関数の引数に fixture 名を書くと、pytest が自動で注入してくれる。

~~~python
async def test_valid_token(rsa_key, verify_token):
    # rsa_key は自動で注入される。自分で呼び出す必要はない。
    token = make_token(rsa_key, make_valid_payload())
    ...
~~~

`scope="session"` は「テスト全体で 1 回だけ実行する」という指定である。`scope` を省略すると「テスト関数ごとに毎回実行する」になる。RSA 鍵の生成は計算コストがかかるため、`scope="session"` で 1 回だけ生成して全テストで使い回している。

------

## patch（モック）とは

`patch` は「本物の代わりに偽物を使う仕組み」である。

このプロジェクトのテストでは、JWT の署名検証を行うために Keycloak から JWKS（公開鍵セット）を取得する処理がある。しかしテスト環境に Keycloak は存在しないため、そのまま実行すると接続エラーになってしまう。

`patch` を使うと、「Keycloak への HTTP 通信」を「あらかじめ用意した偽の JWKS を返す関数」に差し替えられる。

~~~python
with patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks)):
    # この with ブロックの中だけ、load_jwks が偽物になる
    await verify(authorization=f"Bearer {tampered}")
~~~

`with` ブロックを抜けると、`load_jwks` は本物に戻る。

------

## 非同期テストとは

FastAPI の処理関数は `async def` で書かれており、通常の関数とは異なる非同期関数である。テストもそれに合わせて `async def` で書く必要がある。

~~~python
async def test_valid_token(rsa_key, verify_token) -> None:
    claims = await verify_token(authorization=f"Bearer {token}")
~~~

pytest は通常 `async def` の関数を実行できないが、`pytest-asyncio` プラグインを導入することで対応できる。`pyproject.toml` に以下を設定することで、`@pytest.mark.asyncio` マーカーなしでも非同期テストを実行できる。

~~~toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
~~~

`AsyncMock` は「非同期関数の偽物を作るためのクラス」である。`patch` と組み合わせて使う。

~~~python
patch("auth.load_jwks", new=AsyncMock(return_value=public_jwks))
#                            ^^^^^^^^
#                            非同期関数の偽物として動作する
~~~

------

## 関連ドキュメント

- [10_SetupJWTEdgeCaseTests.md](../10_SetupJWTEdgeCaseTests.md) — 本辞書を前提知識として使うハンズオン章
- [05_TokenClaimsAndValidation.md](./05_TokenClaimsAndValidation.md) — JWT の claim と検証順序
