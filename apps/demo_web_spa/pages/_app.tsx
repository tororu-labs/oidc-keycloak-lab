import type { AppProps } from "next/app"
import { TokenProvider } from "@/contexts/TokenContext"

export default function App({ Component, pageProps }: AppProps) {
  return (
    <TokenProvider>
      <Component {...pageProps} />
    </TokenProvider>
  )
}
