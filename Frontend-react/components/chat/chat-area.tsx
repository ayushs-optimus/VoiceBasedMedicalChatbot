'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Conversation, Message } from '@/types/chat';
import { useRouter } from 'next/navigation';
import { useSession } from '@/hooks/use-session';
import { NavModeToggle } from '@/components/ui/navigation';
import {
  Send,
  Bot,
  ThumbsUp,
  ThumbsDown,
  Copy,
  RotateCcw,
  Sparkles,
  Search,
  Zap,
} from 'lucide-react';

interface ChatAreaProps {
  conversation?: Conversation;
  onUpdateConversation: (conversationId: string, messages: Message[]) => void;
  onNewConversation: () => void;
  onSendPrompt?: (promptOverride: string) => void;
}

export function ChatArea({
  conversation,
  onUpdateConversation,
  onNewConversation,
  onSendPrompt,
}: ChatAreaProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { session } = useSession();
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [conversation?.messages]);

  const handleSendMessage = async (promptOverride?: string) => {
    const userInput = promptOverride || input;
    if (!userInput.toString().trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: userInput.trim(),
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
      const response = await fetch(
        'https://containermedchat.thankfulsky-358fb2d4.westus2.azurecontainerapps.io/api/chat/completions',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session?.accessToken || ''}`,
          },
          body: JSON.stringify({
            query: userMessage.content,
            user_id: session?.user.id,
            session_id: conversation.id,
            stream: true,
            roles: session?.user.roles || [],
          }),
          signal: controller.signal,
        }
      );

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

          chunk.split('\n').forEach((line) => {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') return;

              try {
                const json = JSON.parse(data);
                if (json.content) {
                  aiMessage.content += json.content;
                  onUpdateConversation(conversation.id, [...newMessages, aiMessage]);
                }
              } catch {}
            }
          });
        }
        setIsLoading(false);
      };

      readStream();
    } catch (err) {
      console.error('Streaming error', err);
      setIsLoading(false);
    }
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

  const handleQuickPrompt = async (prompt: string) => {
    setInput('');
    if (onSendPrompt) {
      setIsLoading(true);
      await onSendPrompt(prompt);
      setIsLoading(false);
    }
  };

  const QuickPrompts = () => {
    const prompts = [
      {
        icon: <Zap className="h-5 w-5 text-orange-500" />,
        label: 'What is the medical history of charles bankes',
      },
      {
        icon: <Search className="h-5 w-5 text-yellow-500" />,
        label: 'Give me the name of a patient with diabetes',
      },
      {
        icon: <Search className="h-5 w-5 text-blue-500" />,
        label: 'what is the treatment give to patient Elizabeth guzman',
      },
      {
        icon: <Zap className="h-5 w-5 text-pink-500" />,
        label: 'what is the patient id of Elizabeth',
      },
    ];

    return (
      <div className="flex flex-col items-center justify-center px-4 text-center">
        <h2 className="text-2xl font-bold mb-6">What can I help with?</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-3xl">
          {prompts.map((prompt, i) => (
            <div
              key={i}
              onClick={() => handleQuickPrompt(prompt.label)}
              className="flex items-center gap-3 p-4 border rounded-xl bg-muted/30 cursor-pointer hover:bg-muted transition min-h-[80px] min-w-[320px]"
            >
              <div className="p-2 bg-muted rounded-md">{prompt.icon}</div>
              <span className="text-sm font-medium whitespace-normal break-words">
                {prompt.label}
              </span>
              <span className="ml-auto text-muted-foreground text-lg">+</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col gradient-aurora pt-20">
        <NavModeToggle />
        <div className="text-center">
          <div className="p-6 rounded-full bg-primary/10 mx-auto mb-4 w-fit">
            <Sparkles className="h-12 w-12 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Welcome to MediChat A.I+</h2>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            Start a new conversation and experience the power of advanced Medical AI assistance.
          </p>
          <QuickPrompts />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col gradient-aurora">
      <NavModeToggle />
      <ScrollArea className="flex-1 p-6 pt-24" ref={scrollAreaRef}>
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
                onClick={() => handleSendMessage()}
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