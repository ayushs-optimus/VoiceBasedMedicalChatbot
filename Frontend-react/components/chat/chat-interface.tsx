'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from './sidebar';
import { ChatArea } from './chat-area';
import { Conversation, Message } from '@/types/chat';
import { useSession } from '@/hooks/use-session';

export function ChatInterface() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const { session } = useSession();

  useEffect(() => {
    // Load conversations from localStorage
    const savedConversations = localStorage.getItem('chatai_conversations');
    if (savedConversations) {
      try {
        const parsed = JSON.parse(savedConversations);
        setConversations(parsed);
        if (parsed.length > 0) {
          setActiveConversationId(parsed[0].id);
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
      }
    }
  }, []);

  useEffect(() => {
    // Save conversations to localStorage
    localStorage.setItem('chatai_conversations', JSON.stringify(conversations));
  }, [conversations]);

  const createNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    
    setConversations(prev => [newConversation, ...prev]);
    setActiveConversationId(newConversation.id);
  };

  const updateConversation = (conversationId: string, messages: Message[]) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { 
              ...conv, 
              messages, 
              updatedAt: new Date(),
              title: messages.length > 0 ? messages[0].content.slice(0, 50) + '...' : 'New Conversation'
            }
          : conv
      )
    );
  };

  const deleteConversation = (conversationId: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
    if (activeConversationId === conversationId) {
      const remaining = conversations.filter(conv => conv.id !== conversationId);
      setActiveConversationId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  const activeConversation = conversations.find(conv => conv.id === activeConversationId);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
        onNewConversation={createNewConversation}
        onDeleteConversation={deleteConversation}
        user={session?.user}
      />
      <ChatArea
        conversation={activeConversation}
        onUpdateConversation={updateConversation}
        onNewConversation={createNewConversation}
      />
    </div>
  );
}