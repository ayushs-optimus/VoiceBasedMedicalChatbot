'use client';

import { useMsal } from '@azure/msal-react';
import { loginRequest } from '../auth/msalRequests'; // You define this
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bot, Microscope as Microsoft } from 'lucide-react';
import { useSessionContext } from '../providers/session-provider';
import { Session } from 'inspector';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
// import { useRouter } from 'next/navigation';
export function LoginPage() {
  const { login } = useSessionContext();
  const { instance } = useMsal();
  const [isLoading, setIsLoading] = useState(false);
  // const router = useRouter();
 const handleMicrosoftLogin = async () => {
  setIsLoading(true);
  try {
    console.log("Starting Microsoft login...");

    let result;

    // If no active account, skip silent and go straight to login
    const accounts = instance.getAllAccounts();

    if (accounts.length === 0) {
      // Not logged in yet, show login popup
      result = await instance.loginPopup(loginRequest);
      instance.setActiveAccount(result.account);
      console.log("Login successful.");
    } else {
      // Already logged in, try silent first
      result = await instance.acquireTokenSilent({
        ...loginRequest,
        account: accounts[0] // ✅ specify the account
      });
    }

    if (!result.account) {
      throw new Error("No account returned from login.");
    }

    const userSession = {
      user: {
        id: result.account.homeAccountId,
        name: result.account.name || '',
        email: result.account.username || '',
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(result.account.name || 'User')}`,
        roles: result.account.idTokenClaims?.roles || [] // ✅ Add roles here
      },
      accessToken: result.accessToken
    };

    console.log("User session created: %o", userSession);
    instance.setActiveAccount(result.account); // ✅ set active account globally
    console.log("Active account set:", result.account.idTokenClaims?.roles);
    login(userSession);
  } catch (err) {
    console.error("Login failed:", err);
  } finally {
    setIsLoading(false);
  }
};


  return (
    <div className="min-h-screen flex items-center justify-center gradient-aurora p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full bg-primary/10">
              <Bot className="h-8 w-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">MediChat</CardTitle>
          <CardDescription>
            Sign in to continue.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleMicrosoftLogin}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            <Microsoft className="mr-2 h-5 w-5" />
            {isLoading ? 'Signing in...' : 'Sign in with Microsoft'}
          </Button>
          <p className="text-xs text-muted-foreground text-center mt-4">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
