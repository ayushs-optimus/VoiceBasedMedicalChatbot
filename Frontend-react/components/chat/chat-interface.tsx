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
    return newConversation;
  };

  const updateConversation = (conversationId: string, messages: Message[]) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.id === conversationId
          ? {
              ...conv,
              messages,
              updatedAt: new Date(),
              title: messages.length > 0 ? messages[0].content.slice(0, 50) + '...' : 'New Conversation',
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

  const handleSendMessage = async (promptOverride?: string) => {
    const userInput = (promptOverride ?? '').toString().trim();
    if (!userInput) return;

    let conv = activeConversation;
    if (!conv) {
      conv = createNewConversation();
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: userInput,
      role: 'user',
      timestamp: new Date(),
    };

    const newMessages = [...(conv?.messages || []), userMessage];
    updateConversation(conv.id, newMessages);

    try {
      const controller = new AbortController();
      const response = await fetch('https://containermedchat.thankfulsky-358fb2d4.westus2.azurecontainerapps.io/api/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || ''}`,
        },
        body: JSON.stringify({
          query: userInput,
          user_id: session?.user.id,
          session_id: conv.id,
          stream: true,
          roles: session?.user.roles || [],
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) throw new Error(`API error: ${response.statusText}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '',
        role: 'assistant',
        timestamp: new Date(),
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });

        chunk.split('\n').forEach(line => {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;

            try {
              const json = JSON.parse(data);
              if (json.content) {
                aiMessage.content += json.content;
                updateConversation(conv!.id, [...newMessages, aiMessage]);
              }
            } catch {}
          }
        });
      }
    } catch (err) {
      console.error('Streaming error', err);
    }
  };

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
        onSendPrompt={handleSendMessage}
      />
    </div>
  );
}
