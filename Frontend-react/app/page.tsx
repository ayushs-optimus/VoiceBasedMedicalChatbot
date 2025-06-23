'use client';

import { useState, useEffect } from 'react';
import { useSession } from '@/hooks/use-session';
import { LoginPage } from '@/components/auth/login-page';
import { ChatInterface } from '@/components/chat/chat-interface';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export default function Home() {
  const { session, isLoading } = useSession();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-aurora">
        <LoadingSpinner />
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  return <ChatInterface />;
}