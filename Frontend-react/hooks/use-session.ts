'use client';

import { useSessionContext } from '@/components/providers/session-provider';

export function useSession() {
  const { session, isLoading, login, logout } = useSessionContext();
  
  return {
    session,
    isLoading,
    login,
    logout,
  };
}