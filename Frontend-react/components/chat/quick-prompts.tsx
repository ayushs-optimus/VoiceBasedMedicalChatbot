// components/chat/quick-prompts.tsx
'use client';

import { Music, DollarSign, Search, Zap } from 'lucide-react';

const prompts = [
  {
    icon: <Zap className="h-5 w-5 text-orange-500" />,
    label: 'List all the speakers',
  },
  {
    icon: <Search className="h-5 w-5 text-yellow-500" />,
    label: 'Give me the cheapest Product',
  },
  {
    icon: <Search className="h-5 w-5 text-blue-500" />,
    label: 'Tell me the details of product with ID 1',
  },
  {
    icon: <Zap className="h-5 w-5 text-pink-500" />,
    label: 'List all sports products',
  },
];

export function QuickPrompts() {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4 text-center">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-md">
        {prompts.map((prompt, i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-4 border rounded-xl bg-muted/30 cursor-pointer hover:bg-muted transition"
          >
            <div className="p-2 bg-muted rounded-md">{prompt.icon}</div>
            <span className="text-sm font-medium">{prompt.label}</span>
            <span className="ml-auto text-muted-foreground text-lg">+</span>
          </div>
        ))}
      </div>
    </div>
  );
}
