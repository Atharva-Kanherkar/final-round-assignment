import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'AI Mock Interview System',
    template: '%s | AI Mock Interview',
  },
  description: 'Production-grade AI-powered interview coach that conducts intelligent technical interviews with multi-agent architecture, real-time feedback, and comprehensive evaluation',
  keywords: [
    'AI interview',
    'mock interview',
    'technical interview practice',
    'AI feedback',
    'interview preparation',
    'coding interview',
    'system design interview',
    'interview coach',
  ],
  authors: [{ name: 'Atharva Kanherkar' }],
  creator: 'Atharva Kanherkar',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://final-round-assignment.vercel.app',
    title: 'AI Mock Interview System',
    description: 'Practice technical interviews with AI-powered feedback and comprehensive evaluation',
    siteName: 'AI Mock Interview System',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI Mock Interview System',
    description: 'Practice technical interviews with AI-powered feedback',
  },
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/icon.png', type: 'image/png', sizes: '32x32' },
    ],
    apple: [
      { url: '/apple-icon.png', type: 'image/png', sizes: '180x180' },
    ],
  },
  manifest: '/site.webmanifest',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
