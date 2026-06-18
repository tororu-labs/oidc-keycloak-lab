import { createContext, useContext, useState, ReactNode } from "react"

interface TokenContextValue {
  accessToken: string | null
  setAccessToken: (token: string | null) => void
}

const TokenContext = createContext<TokenContextValue | null>(null)

// アプリ全体で access token をメモリ内に保持するための Provider
export function TokenProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null)
  return (
    <TokenContext.Provider value={{ accessToken, setAccessToken }}>
      {children}
    </TokenContext.Provider>
  )
}

export function useToken(): TokenContextValue {
  const ctx = useContext(TokenContext)
  if (!ctx) throw new Error("useToken は TokenProvider の内側で使う必要があります")
  return ctx
}
