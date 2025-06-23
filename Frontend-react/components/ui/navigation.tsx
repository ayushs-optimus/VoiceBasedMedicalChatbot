'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { MessageSquare, Mic } from 'lucide-react';

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
      <div className="flex items-center gap-2 bg-card/80 backdrop-blur-sm border border-border rounded-full p-1">
        <Button
          asChild
          variant={pathname === '/' ? 'default' : 'ghost'}
          size="sm"
          className="rounded-full"
        >
          <Link href="/">
            <MessageSquare className="h-4 w-4 mr-2" />
            Text Chat
          </Link>
        </Button>
        <Button
          asChild
          variant={pathname === '/voice' ? 'default' : 'ghost'}
          size="sm"
          className="rounded-full"
        >
          <Link href="/voice">
            <Mic className="h-4 w-4 mr-2" />
            Voice Chat
          </Link>
        </Button>
      </div>
    </nav>
  );
}