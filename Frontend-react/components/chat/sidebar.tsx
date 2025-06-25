'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Conversation } from '@/types/chat';
import { useSession } from '@/hooks/use-session';
import { 
  Plus, 
  Search, 
  Settings, 
  LogOut, 
  Trash2, 
  MessageSquare,
  Bot,
  MoreVertical
} from 'lucide-react';
import { format } from 'date-fns';
import { stringify } from 'node:querystring';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => Conversation;
  onDeleteConversation: (id: string) => void;
  user?: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
    roles?: string[]; // Optional roles for the user
  };
}

export function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  user
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const { logout } = useSession();

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

 const getTimeAgo = (input: Date | string) => {
  const now = new Date();
  const date = new Date(input); // Convert string to Date if necessary

  if (isNaN(date.getTime())) return 'Invalid date'; // Optional safety

  const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffInDays === 0) return 'Today';
  if (diffInDays === 1) return 'Yesterday';
  if (diffInDays < 7) return `${diffInDays} days ago`;
  return format(date, 'MMM d, yyyy');
};

  return (
    <div className="w-80 bg-card border-r border-border gradient-aurora-sidebar flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">MediChat A.I+</h1>
        </div>
        
        <Button 
          onClick={onNewConversation}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
          size="sm"
        >
          <Plus className="h-4 w-4 mr-2" />
          New chat
        </Button>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-hidden">
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-muted-foreground">Your conversations</span>
            <Badge variant="secondary" className="text-xs">
              {conversations.length}
            </Badge>
          </div>
        </div>
        
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-2">
            {filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`group relative p-3 rounded-lg cursor-pointer sidebar-item ${
                  activeConversationId === conversation.id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'hover:bg-muted/50'
                }`}
                onClick={() => onSelectConversation(conversation.id)}
              >
                <div className="flex items-start gap-3">
                  <MessageSquare className="h-4 w-4 text-muted-foreground mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {conversation.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {getTimeAgo(conversation.updatedAt)}
                    </p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conversation.id);
                        }}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.avatar} alt={user?.name} />
            <AvatarFallback>{user?.name?.[0]}</AvatarFallback>
          </Avatar>
           <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>

            {/* ✅ Display roles here */}
            {user?.roles && user.roles.length > 0 && (
              <p className="text-xs text-muted-foreground truncate">
                {user.roles.join(', ')}
              </p>
            )}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <Settings className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuItem onClick={logout}>
                <LogOut className="h-4 w-4 mr-2" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  );
}