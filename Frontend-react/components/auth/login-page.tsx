'use client';

import { useMsal } from '@azure/msal-react';
import { loginRequest } from '../auth/msalRequests'; // You define this
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bot, Microscope as Microsoft } from 'lucide-react';
import { useSessionContext } from '../providers/session-provider';
// import { useRouter } from 'next/navigation';
export function LoginPage() {
  const { login } = useSessionContext();
  const { instance } = useMsal();
  const [isLoading, setIsLoading] = useState(false);
  // const router = useRouter();
  const handleMicrosoftLogin = async () => {
    setIsLoading(true);
    try {
      const result = await instance.loginPopup(loginRequest);

      if (!result.account) {
        throw new Error("No account returned from login.");
      }

      // Create your session object
      const userSession = {
        user: {
          id: result.account.homeAccountId, // or localAccountId
          name: result.account.name || '',
          email: result.account.username || '',
          avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(result.account.name || 'User')}`
        },
        accessToken: result.accessToken
      };
      login(userSession); // Store in localStorage + context
      console.log("Login successful, session stored.", result.idTokenClaims);
      // const roles = result.idTokenClaims?.roles || [];
      // console.log("User roles:", roles);
      // router.push('/'); // Redirect to home page after login
    } catch (err) {
      console.error('Login failed:', err);
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
