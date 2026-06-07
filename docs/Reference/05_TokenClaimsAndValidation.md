# 05 Token Claims And Validation

## 目的

このドキュメントは、`docs/08_SetupAudienceValidation.md` までで扱った JWT 検証の内容を座学として整理するものである。

- access token に含まれる主要な claim の意味と役割
- Backend API が検証する claim の順序と各検証の意図
- `aud` と `azp` の使い分け
- joserfc の `JWTClaimsRegistry` の仕組みと例外型の対応

------

## access token に含まれる主要な claim

Keycloak が発行する access token には、次のような claim が含まれる。

| claim | 意味 | この repo での値の例 |
|-------|------|---------------------|
| `iss` | token を発行した認証サーバー | `http://localhost:8080/realms/lab` |
| `sub` | token の主体（user の一意識別子） | UUID 形式の文字列 |
| `aud` | token を受け取るべきサービス | `["account", "demo-api"]` |
| `azp` | token を要求した client | `demo-bff` |
| `exp` | token の有効期限（Unix 時刻） | 発行時刻 + 300 秒など |
| `iat` | token の発行時刻（Unix 時刻） | 発行時の Unix 時刻 |
| `realm_access.roles` | user に割り当てられた realm role の一覧 | `["viewer"]`、`["admin"]` など |

実際に token の中身を確認するには、Keycloak 管理コンソールの `Clients > demo-bff > Client scopes > Evaluate > Generated access token` が手軽である。

~~~text
{
  "iss": "http://localhost:8080/realms/lab",
  "sub": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "aud": ["account", "demo-api"],
  "azp": "demo-bff",
  "exp": 1700000300,
  "iat": 1700000000,
  "realm_access": {
    "roles": ["viewer"]
  },
  ...
}
~~~

------

## Backend API が検証する claim の順序と役割

Backend API は、token を受け取ったときに次の順序で検証を行う。

1. **署名の検証**
   - Keycloak の JWKS から公開鍵を取得し、token が改ざんされていないことを確認する
   - 改ざんがあれば以降の claim は信頼できない
2. **`iss` の検証**
   - 期待する Keycloak realm から発行された token であることを確認する
   - 別の IdP や realm から発行された token を弾く
3. **`exp` の検証**
   - token が有効期限内であることを確認する
   - 期限切れの token を再利用した攻撃を防ぐ
4. **`aud` の検証**
   - token が自分のサービス宛てであることを確認する
   - 同じ realm 内の別サービス向けの token が誤って通過することを防ぐ

この順序には意味がある。署名が不正なら claim の値自体が信頼できないため、署名検証を最初に行う。`exp` は token の基本的な有効性、`aud` はサービス宛ての正当性を担保する。

------

## `aud` と `azp` の使い分け

`aud` と `azp` は似ているが役割が異なる。

| claim | 問いかけ | 値の例 |
|-------|---------|--------|
| `aud` | この token を**受け取るべき**のは誰か | `["account", "demo-api"]` |
| `azp` | この token を**要求した**のは誰か | `demo-bff` |

この repo の構成で言えば、次のような関係になる。

- BFF（`demo-bff`）が Keycloak に token を要求する → `azp: demo-bff`
- その token を Backend API（`demo-api`）が受け取る → `aud: demo-api`

`aud` を検証することで、`demo-bff` 宛てに発行された token が `demo-api` を通過できないようにできる。これは confused deputy 問題の基本的な防御策になる。

補足:

- Keycloak はデフォルトで `account` client scope が付くため、`aud` に `account` が含まれることが多い
- `demo-api` を `aud` に追加するには Audience Mapper が必要（`docs/08` 参照）

------

## joserfc の `JWTClaimsRegistry` の仕組み

Backend API では、joserfc の `JWTClaimsRegistry` に検証ルールをまとめ、`jwt.decode` の後に `registry.validate()` を呼んで claim を検証している。

~~~python
registry = jwt.JWTClaimsRegistry(
    iss={"essential": True, "value": settings.issuer},
    aud={"essential": True, "value": settings.expected_audience},
    leeway=settings.clock_skew_seconds,
)
result = jwt.decode(token, key_set)
registry.validate(result.claims)
~~~

各フィールドの意味:

| フィールド | 意味 |
|-----------|------|
| `essential: True` | この claim が token に存在しなければ検証失敗にする |
| `value` | claim の値がこの値と一致しなければ検証失敗にする |

`leeway` は `JWTClaimsRegistry` のコンストラクタに渡す。時刻のずれを許容する秒数で、サーバ間のクロックずれを考慮して `exp` の境界付近での不必要な検証失敗を防ぐ。

### 例外型と失敗理由の対応

joserfc が送出する例外型と、それが意味する失敗理由の対応は次のとおり。

| 例外型 | 意味 | ログの `reason` |
|--------|------|----------------|
| `BadSignatureError` | 署名が不正 | `bad_signature` |
| `ExpiredTokenError` | `exp` が期限切れ | `expired_token` |
| `JoseError`（基底クラス） | claim 不一致・claim 欠落など上記以外の JWT 検証エラー | `jose_error` |

`BadSignatureError` と `ExpiredTokenError` は個別に捕捉してエラー内容を明確にし、それ以外（`iss`・`aud` 不一致、`essential` な claim の欠落など）は `JoseError` でまとめて捕捉している（`apps/demo_api/auth.py` 参照）。

------

## 関連ドキュメント

- [08_SetupAudienceValidation.md](../08_SetupAudienceValidation.md)
- [07_SetupTokenValidationAndFailureCases.md](../07_SetupTokenValidationAndFailureCases.md)
- [04_ClientAndTokenRoles.md](./04_ClientAndTokenRoles.md)
- [03_Troubleshooting.md](./03_Troubleshooting.md)
