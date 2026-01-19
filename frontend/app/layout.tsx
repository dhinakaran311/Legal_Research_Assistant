import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { ApolloWrapper } from '@/components/ApolloWrapper';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Legal Research Assistant - AI-Powered Legal Search',
  description: 'AI-powered legal research platform for Indian law with intelligent search through acts, judgments, and legal documents',
  keywords: ['legal research', 'Indian law', 'AI legal assistant', 'legal search'],
  authors: [{ name: 'Legal Research Assistant Team' }],
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <ToastProvider>
            <ApolloWrapper>
              <AuthProvider>
                {children}
              </AuthProvider>
            </ApolloWrapper>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
