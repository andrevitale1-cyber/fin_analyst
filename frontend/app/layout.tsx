import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider
      // AQUI ESTÁ O SEGREDO: Forçamos os links externos direto no código
      signInUrl="https://dashing-ocelot-83.accounts.dev/sign-in"
      signUpUrl="https://dashing-ocelot-83.accounts.dev/sign-up"
      afterSignOutUrl="/"
    >
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}