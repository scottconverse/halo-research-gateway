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
  title: 'Halo Research Gateway — One research plane for every agent',
  description:
    'A DSH-first local MCP gateway for search, crawling, evidence, authenticated research, durable jobs, and operator-authorized web actions.',
  openGraph: {
    title: 'Halo Research Gateway',
    description:
      'One local, source-backed research plane for every agent in the Halo stack.',
    type: 'website',
  },
  twitter: {
    card: 'summary',
    title: 'Halo Research Gateway',
    description:
      'DSH-first research, crawling, evidence, identity, and operator-authorized actions.',
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
