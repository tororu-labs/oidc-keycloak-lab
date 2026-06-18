import { useState } from "react"
import { useToken } from "@/contexts/TokenContext"
import { generateCodeVerifier, generateCodeChallenge } from "@/lib/pkce"

const KEYCLOAK_BASE = process.env.NEXT_PUBLIC_KEYCLOAK_BASE_URL!
const REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM!
const CLIENT_ID = process.env.NEXT_PUBLIC_OIDC_CLIENT_ID!
const APP_BASE = process.env.NEXT_PUBLIC_APP_BASE_URL!
const BACKEND_API = process.env.NEXT_PUBLIC_BACKEND_API_BASE_URL!

export default function Home() {
  const { accessToken, setAccessToken } = useToken()
  const [apiResult, setApiResult] = useState<unknown>(null)
  const [apiStatus, setApiStatus] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  // PKCE フロー開始: verifier を生成して sessionStorage に保存し、Keycloak へリダイレクト
  async function handleLogin() {
    setError(null)
    const verifier = generateCodeVerifier()
    const challenge = await generateCodeChallenge(verifier)
    sessionStorage.setItem("pkce_verifier", verifier)

    const params = new URLSearchParams({
      response_type: "code",
      client_id: CLIENT_ID,
      redirect_uri: `${APP_BASE}/callback`,
      scope: "openid profile email",
      code_challenge: challenge,
      code_challenge_method: "S256",
    })
    window.location.href = `${KEYCLOAK_BASE}/realms/${REALM}/protocol/openid-connect/auth?${params}`
  }

  // ブラウザから Backend API を直接 Bearer token で呼び出す（BFF を経由しない）
  async function handleCallApi() {
    if (!accessToken) return
    setApiResult(null)
    setError(null)
    try {
      const res = await fetch(`${BACKEND_API}/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      setApiStatus(res.status)
      setApiResult(await res.json())
    } catch (e) {
      setError(`API 呼び出し失敗: ${e}`)
    }
  }

  // メモリ上の token をクリアするだけ（Keycloak セッションは残る）
  function handleLogout() {
    setAccessToken(null)
    setApiResult(null)
    setApiStatus(null)
  }

  return (
    <main style={{ fontFamily: "monospace", maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>demo-web-spa（SPA + PKCE）</h1>

      {!accessToken ? (
        <div>
          <p>ログインしていません。</p>
          <button onClick={handleLogin}>Keycloak でログイン（PKCE）</button>
        </div>
      ) : (
        <div>
          <p style={{ color: "green" }}>ログイン済み（access token をメモリ内に保持中）</p>
          <button onClick={handleCallApi} style={{ marginRight: 8 }}>
            Backend API (/me) を直接呼ぶ
          </button>
          <button onClick={handleLogout}>ローカルログアウト</button>

          {error && <p style={{ color: "red" }}>{error}</p>}

          {apiResult !== null && (
            <div>
              <p>ステータス: {apiStatus}</p>
              <pre style={{ background: "#f5f5f5", padding: 12, overflowX: "auto" }}>
                {JSON.stringify(apiResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      <hr style={{ marginTop: 40 }} />
      <p style={{ color: "#888", fontSize: 12 }}>
        token の保管場所: React state（メモリ）/ ページリロードで消える
      </p>
    </main>
  )
}
