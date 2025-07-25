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

  // Function to create and select a new conversation
  const createNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'New Conversation', // Default title for a new chat
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    setConversations(prev => [newConversation, ...prev]); // Add new conversation to the top
    setActiveConversationId(newConversation.id); // Set it as the active one
    return newConversation; // Return the new conversation for immediate use if needed
  };

  // Effect to load conversations from localStorage and set initial active conversation
  useEffect(() => {
    const savedConversations = localStorage.getItem('chatai_conversations');
    let loadedConversations: Conversation[] = [];

    if (savedConversations) {
      try {
        loadedConversations = JSON.parse(savedConversations);
        // Ensure dates are correctly parsed if they were stored as strings
        loadedConversations = loadedConversations.map(conv => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt)
        }));
        setConversations(loadedConversations);
      } catch (error) {
        console.error('Error loading conversations from localStorage:', error);
        // Fallback to empty array if parsing fails
        loadedConversations = [];
      }
    }

    // If no conversations were loaded (or parsing failed), create a new one
    if (loadedConversations.length === 0) {
      // Create a new conversation and set it as active
      // We call createNewConversation directly here because it updates state
      // which will trigger a re-render.
      createNewConversation();
    } else {
      // If conversations were loaded, set the first one as active
      setActiveConversationId(loadedConversations[0].id);
    }
  }, []); // Empty dependency array means this runs once on mount

  // Effect to save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chatai_conversations', JSON.stringify(conversations));
  }, [conversations]);

  const updateConversation = (conversationId: string, messages: Message[]) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.id === conversationId
          ? {
              ...conv,
              messages,
              updatedAt: new Date(),
              // Update title based on the first user message if available
              title: messages.length > 0 && messages[0].role === 'user' ? messages[0].content.slice(0, 50) + '...' : conv.title,
            }
          : conv
      )
    );
  };

  const deleteConversation = (conversationId: string) => {
    setConversations(prev => {
      const filtered = prev.filter(conv => conv.id !== conversationId);
      // If the deleted conversation was active, select the first remaining one or create new
      if (activeConversationId === conversationId) {
        if (filtered.length > 0) {
          setActiveConversationId(filtered[0].id);
        } else {
          // If no conversations left, create a brand new one
          // We can call createNewConversation directly here.
          createNewConversation();
          return []; // Return empty array temporarily, createNewConversation will add the new one
        }
      }
      return filtered;
    });
  };

  const activeConversation = conversations.find(conv => conv.id === activeConversationId);

  // This handleSendMessage is specifically for when ChatArea's onSendPrompt is used.
  // It ensures a conversation exists before sending a message.
  const handleSendMessage = async (promptOverride: string) => {
  const userInput = promptOverride.toString().trim();
  if (!userInput) return;

  let convToUse = activeConversation;
  if (!convToUse) {
    convToUse = createNewConversation();
  }

  const userMessage: Message = {
    id: Date.now().toString(),
    content: userInput,
    role: 'user',
    timestamp: new Date(),
  };

  const currentMessages = convToUse.messages || [];
  const newMessages = [...currentMessages, userMessage];

  updateConversation(convToUse.id, newMessages); // ✅ safe now

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
        session_id: convToUse.id, // ✅ safe now
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
              updateConversation(convToUse!.id, [...newMessages, aiMessage]);

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
    <div className="flex h-screen w-screen bg-background overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
        onNewConversation={createNewConversation} // This is used by the "New chat" button in Sidebar
        onDeleteConversation={deleteConversation}
        user={session?.user}
      />
      <ChatArea
        conversation={activeConversation}
        onUpdateConversation={updateConversation}
        onNewConversation={createNewConversation} // This is used by ChatArea if conversation is null
        onSendPrompt={handleSendMessage} // Pass the integrated send message for quick prompts
      />
    </div>
  );
}