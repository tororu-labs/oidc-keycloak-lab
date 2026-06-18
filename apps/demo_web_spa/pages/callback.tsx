import { useEffect, useState } from "react"
import { useRouter } from "next/router"
import { useToken } from "@/contexts/TokenContext"

const KEYCLOAK_BASE = process.env.NEXT_PUBLIC_KEYCLOAK_BASE_URL!
const REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM!
const CLIENT_ID = process.env.NEXT_PUBLIC_OIDC_CLIENT_ID!
const APP_BASE = process.env.NEXT_PUBLIC_APP_BASE_URL!

export default function Callback() {
  const router = useRouter()
  const { setAccessToken } = useToken()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get("code")
    const error = params.get("error")

    // Keycloak がエラーを返してきた場合（例: アクセス拒否）
    if (error) {
      setErrorMessage(`認証エラー: ${error} - ${params.get("error_description") ?? ""}`)
      return
    }

    const verifier = sessionStorage.getItem("pkce_verifier")
    if (!code || !verifier) {
      setErrorMessage("code または code_verifier が見つかりません。最初からやり直してください。")
      return
    }

    // 認可コードと code_verifier を使って token endpoint からトークンを取得する
    ;(async () => {
      try {
        const res = await fetch(
          `${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/token`,
          {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded; charset=utf-8" },
            body: new URLSearchParams({
              grant_type: "authorization_code",
              client_id: CLIENT_ID,
              code,
              redirect_uri: `${APP_BASE}/callback`,
              code_verifier: verifier,
            }),
          }
        )
        const tokens = await res.json()
        if (!res.ok) {
          setErrorMessage(`Token 取得失敗: ${tokens.error} - ${tokens.error_description ?? ""}`)
          return
        }

        // 使い終わった verifier は即削除する
        sessionStorage.removeItem("pkce_verifier")
        setAccessToken(tokens.access_token)
        router.push("/")
      } catch (e) {
        setErrorMessage(`Token エンドポイント呼び出し失敗: ${e}`)
      }
    })()
  }, [])

  if (errorMessage) {
    return (
      <main style={{ fontFamily: "monospace", maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
        <h1>認証エラー</h1>
        <p style={{ color: "red" }}>{errorMessage}</p>
        <a href="/">トップに戻る</a>
      </main>
    )
  }

  return (
    <main style={{ fontFamily: "monospace", maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <p>認証処理中...</p>
    </main>
  )
}
