'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

interface Session {
  user: User;
  accessToken: string;
}

interface SessionContextType {
  session: Session | null;
  isLoading: boolean;
  login: (session: Session) => void;
  logout: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session in localStorage
    const savedSession = localStorage.getItem('chatai_session');
    if (savedSession) {
      try {
        const parsedSession = JSON.parse(savedSession);
        setSession(parsedSession);
      } catch (error) {
        console.error('Error parsing saved session:', error);
        localStorage.removeItem('chatai_session');
      }
    }
    setIsLoading(false);
  }, []);

  const login = (newSession: Session) => {
    setSession(newSession);
    localStorage.setItem('chatai_session', JSON.stringify(newSession));
  };

  const logout = () => {
    setSession(null);
    localStorage.removeItem('chatai_session');
    localStorage.removeItem('chatai_conversations');
  };

  return (
    <SessionContext.Provider value={{ session, isLoading, login, logout }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSessionContext() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSessionContext must be used within a SessionProvider');
  }
  return context;
}