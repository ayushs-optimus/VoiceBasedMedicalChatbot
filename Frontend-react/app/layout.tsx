import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { SessionProvider } from '@/components/providers/session-provider';
import { MsalProviderWrapper } from '@/components/providers/msal-provider-wrapper';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MediChat+ - Advanced Medical AI Assistant',
  description: 'Your Intelligent Medical Assistant for Advanced Healthcare Conversations',
};

export default function RootLayout({
  
  children,
}: {
  children: React.ReactNode;
}) {
    
  return (
    <html lang="en">
      <body className={inter.className}>
        <MsalProviderWrapper>
          <SessionProvider>
            {children}
          </SessionProvider>
        </MsalProviderWrapper>
      </body>
    </html>
  );
}
