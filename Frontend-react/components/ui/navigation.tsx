// components/nav-mode-toggle.tsx
'use client';

import { useRouter, usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { MessageSquare, Music } from 'lucide-react';

export function NavModeToggle() {
  const router = useRouter();
  const pathname = usePathname();

  const isTextChat = pathname.includes('/text') || pathname === '/';

  return (
    <div className="flex justify-center py-2 gradient-aurora">
      <div className="bg-background border border-border rounded-full px-4 py-2 flex gap-2">
        <Button
          variant={isTextChat ? 'outline' : 'ghost'}
          size="sm"
          className={isTextChat ? 'text-primary font-medium' : 'text-muted-foreground'}
          onClick={() => router.push('/')}
        >
          <MessageSquare className="h-4 w-4 mr-2" /> Text Chat
        </Button>
        <Button
          variant={!isTextChat ? 'outline' : 'ghost'}
          size="sm"
          className={!isTextChat ? 'text-primary font-medium' : 'text-muted-foreground'}
          onClick={() => router.push('/voice')}
        >
          <Music className="h-4 w-4 mr-2" /> Voice Chat
        </Button>
      </div>
    </div>
  );
}