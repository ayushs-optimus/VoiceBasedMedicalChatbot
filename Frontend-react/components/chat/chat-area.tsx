'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Conversation, Message } from '@/types/chat';
import { useSession } from '@/hooks/use-session';
import { 
  Send, 
  Bot, 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  RotateCcw,
  Sparkles,
  MessageSquare
} from 'lucide-react';

interface ChatAreaProps {
  conversation?: Conversation;
  onUpdateConversation: (conversationId: string, messages: Message[]) => void;
  onNewConversation: () => void;
}

export function ChatArea({ conversation, onUpdateConversation, onNewConversation }: ChatAreaProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { session } = useSession();
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [conversation?.messages]);

  const handleSendMessage = async () => {
  if (!input.trim()) return;

  const userMessage: Message = {
    id: Date.now().toString(),
    content: input.trim(),
    role: 'user',
    timestamp: new Date(),
  };

  if (!conversation) {
    onNewConversation();
    return;
  }

  const newMessages = [...conversation.messages, userMessage];
  onUpdateConversation(conversation.id, newMessages);
  setInput('');
  setIsLoading(true);

  try {
    const controller = new AbortController();
    const response = await fetch("https://containermedchat.thankfulsky-358fb2d4.westus2.azurecontainerapps.io/api/chat/completions", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.accessToken || ''}`,
      },
      body: JSON.stringify({
        query: userMessage.content,
        user_id: session?.user.id,
        session_id: conversation.id,
        stream: true
      }),
      signal: controller.signal
    });

    if (!response.ok || !response.body) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      role: 'assistant',
      timestamp: new Date(),
    };

    const readStream = async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });

        chunk.split('\n').forEach(line => {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") return;

            try {
              const json = JSON.parse(data);
              if (json.content) {
                aiMessage.content += json.content;
                onUpdateConversation(conversation.id, [...newMessages, aiMessage]);
              }
              // handle thinking_process if needed
            } catch {}
          }
        });
      }
      setIsLoading(false);
    };

    readStream();
  } catch (err) {
    console.error("Streaming error", err);
    setIsLoading(false);
  }
};


  const generateAIResponse = (userInput: string): string => {
    const responses = [
      "I understand your question about " + userInput.slice(0, 30) + "... Let me provide you with a comprehensive answer based on my knowledge.",
      "That's an interesting question! Here's what I can tell you about that topic...",
      "I'd be happy to help you with that. Based on the information you've provided, here are some insights...",
      "Thank you for your question. Let me break this down for you in a clear and helpful way..."
    ];
    
    return responses[Math.floor(Math.random() * responses.length)] + "\n\nThis is a simulated AI response. In a real implementation, this would be connected to an actual AI service like OpenAI's GPT or similar language models.";
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center gradient-aurora">
        <div className="text-center">
          <div className="p-6 rounded-full bg-primary/10 mx-auto mb-4 w-fit">
            <Sparkles className="h-12 w-12 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Welcome to CHAT A.I+</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Start a new conversation and experience the power of advanced AI assistance.
          </p>
          <Button onClick={onNewConversation} size="lg">
            <MessageSquare className="h-5 w-5 mr-2" />
            Start Chatting
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col gradient-aurora">
      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-6" ref={scrollAreaRef}>
        <div className="max-w-4xl mx-auto space-y-6">
          {conversation.messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarFallback className="bg-primary/10">
                    <Bot className="h-4 w-4 text-primary" />
                  </AvatarFallback>
                </Avatar>
              )}
              
              <div
                className={`message-bubble rounded-lg p-4 max-w-2xl ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card border border-border'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                  {message.role === 'assistant' && (
                    <div className="flex gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <ThumbsUp className="h-3 w-3" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <ThumbsDown className="h-3 w-3" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 w-8 p-0"
                        onClick={() => copyToClipboard(message.content)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <RotateCcw className="h-3 w-3" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              {message.role === 'user' && (
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarImage src={session?.user?.avatar} alt={session?.user?.name} />
                  <AvatarFallback>{session?.user?.name?.[0]}</AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-4 justify-start">
              <Avatar className="h-8 w-8 flex-shrink-0">
                <AvatarFallback className="bg-primary/10">
                  <Bot className="h-4 w-4 text-primary" />
                </AvatarFallback>
              </Avatar>
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-75"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-150"></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-4 items-end">
            <div className="flex-1 relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="What's in your mind..."
                className="chat-input resize-none pr-12"
                rows={1}
                disabled={isLoading}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!input.trim() || isLoading}
                size="sm"
                className="absolute right-2 bottom-2"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}