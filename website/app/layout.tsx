import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://halo-research-gateway.sconverse.chatgpt.site'),
  title: 'Halo Research Gateway 0.2.0 — One research plane for every agent',
  description:
    'A DSH-first local MCP gateway for deep research, crawling, GitHub, transcripts, communities, authenticated identity, durable jobs, and operator-authorized web actions.',
  openGraph: {
    title: 'Halo Research Gateway 0.2.0',
    description:
      'One local, source-backed research plane for every agent in the Halo stack.',
    type: 'website',
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: 'Halo Research Gateway 0.2.0 — One research plane. Every agent.',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Halo Research Gateway 0.2.0',
    description:
      'DSH-first research, crawling, evidence, identity, and operator-authorized actions.',
    images: ['/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
