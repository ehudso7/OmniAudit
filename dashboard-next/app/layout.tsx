import type { Metadata, Viewport } from 'next';
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import './globals.css';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { Toaster } from '@/components/ui/toaster';

export const metadata: Metadata = {
  title: {
    template: '%s | OmniAudit',
    default: 'OmniAudit - AI-Powered Code Audit Platform',
  },
  description:
    'Enterprise-grade code security, quality, and performance analysis powered by AI',
  keywords: ['code audit', 'security', 'AI', 'code quality', 'vulnerability scanner'],
  authors: [{ name: 'OmniAudit Team' }],
  creator: 'OmniAudit',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://omniaudit.dev',
    title: 'OmniAudit - AI-Powered Code Audit Platform',
    description: 'Enterprise-grade code security, quality, and performance analysis',
    siteName: 'OmniAudit',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'OmniAudit',
    description: 'AI-Powered Code Audit Platform',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
  ],
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${GeistSans.variable} ${GeistMono.variable} antialiased bg-background text-foreground`}
      >
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
