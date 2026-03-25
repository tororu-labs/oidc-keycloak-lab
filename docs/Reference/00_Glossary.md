# 00 Glossary

## 目的

このドキュメントは、`docs/04` から `docs/06` と `docs/Reference/` で繰り返し使う用語を短く整理するものである。

------

## Authorization Code Flow

ブラウザを使って IdP にログインし、認可コードを経由して token を取得する OIDC / OAuth 2.0 の基本フロー。

## callback

IdP が認可コードや認証結果を返すために、アプリ側で待ち受ける URL。

## confidential client

client secret を安全に保持できる前提の client。サーバ側アプリや BFF で使いやすい。

## public client

client secret を安全に保持できない前提の client。ブラウザアプリやネイティブアプリで使われることが多い。

## BFF

Browser と backend の間に立ち、token をブラウザへ直接渡さずに扱う構成パターン。

## session

アプリがログイン状態を保持するための仕組み。今回の repo では主に BFF 側で使う。

## access token

API へアクセスする権限を示す token。Backend API はこれを検証して認可判定を行う。

## ID token

ログインした user に関する情報を client が確認するための token。API 認可そのものに使う前提ではない。

## refresh token

期限切れになった access token を再取得するための token。

## issuer (`iss`)

token を発行した主体を表す値。今回の repo では Keycloak の realm URL が入る。

## audience (`aud`)

その token が主に誰向けかを表す値。API 保護では重要だが、この repo ではまず `iss` と `exp` の検証を優先している。

## authorized party (`azp`)

どの client が token に関係しているかを見るための claim。Keycloak の token 比較では `demo-web` などの client がここに出る。

## subject (`sub`)

その token が指している user の識別子。表示用 username より機械的な識別子として安定しやすい。

## expiration time (`exp`)

token の失効時刻。Backend API は現在時刻と比較して期限切れでないことを確認する。

## issued at (`iat`)

token の発行時刻。

## preferred_username

表示用 username に近い claim。画面表示には便利だが、識別子そのものとしては `sub` と役割が異なる。

## JWKS

JWT の署名検証に使う公開鍵セット。

## realm role

realm 全体で使う権限ラベル。今回の repo では `viewer` や `admin` が該当する。

## client role

特定 client に閉じた権限ラベル。今回の repo では主に realm role を使っている。

## client

Keycloak を利用するアプリケーション側の設定単位。今回の repo では `demo-web` や `demo-bff` が該当する。

## client scope

token にどの claim を載せるか、どの scope を扱うかをまとめる設定単位。user や role そのものではなく、token の中身の出し方に近い。

## redirect_uri

IdP がログイン後にブラウザを戻してよい先の URL。Keycloak では登録済み値と一致しないと認可開始を拒否する。

## state

認可開始前に client が生成し、callback で戻ってきた値と照合するパラメータ。ログイン要求と callback の対応確認に使う。

## nonce

主に ID token とログイン要求を結び付けるための値。`state` と似て見えるが、token と要求の対応確認に寄っている。

## PKCE

認可コード横取り対策として使う仕組み。public client で特に重要で、認可開始時の要求と token 交換を結び付ける。
