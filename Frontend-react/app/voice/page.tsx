'use client';

import { VoiceChatInterface } from '@/components/voice/voice-chat-interface';
import { useSession } from '@/hooks/use-session';
import { LoginPage } from '@/components/auth/login-page';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useState, useEffect } from 'react';

export default function VoicePage() {
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

  return <VoiceChatInterface />;
}