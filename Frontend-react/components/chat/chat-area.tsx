'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
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
  onNewConversation: () => Conversation;
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
  const [promptSent, setPromptSent] = useState(false);
  const [likedMessages, setLikedMessages] = useState<Set<string>>(new Set());
  const [dislikedMessages, setDislikedMessages] = useState<Set<string>>(new Set());

  const { session } = useSession();
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const savedLikes = sessionStorage.getItem('chatai_liked_messages');
    if (savedLikes) {
      setLikedMessages(new Set(JSON.parse(savedLikes)));
    }
    const savedDislikes = sessionStorage.getItem('chatai_disliked_messages');
    if (savedDislikes) {
      setDislikedMessages(new Set(JSON.parse(savedDislikes)));
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem('chatai_liked_messages', JSON.stringify(Array.from(likedMessages)));
  }, [likedMessages]);

  useEffect(() => {
    sessionStorage.setItem('chatai_disliked_messages', JSON.stringify(Array.from(dislikedMessages)));
  }, [dislikedMessages]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [conversation?.messages]);

  useEffect(() => {
    if (conversation && conversation.messages.length === 0 && promptSent) {
      setPromptSent(false);
    }
  }, [conversation, promptSent]);

  const handleSendMessage = async (promptOverride?: string) => {
    const userInput = promptOverride || input;
    if (!userInput.toString().trim()) return;

    let convToUse = conversation;
    if (!convToUse) {
      convToUse = onNewConversation(); // Ensure onNewConversation returns the new conversation
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: userInput.trim(),
      role: 'user',
      timestamp: new Date(),
    };

    const newMessages = [...(convToUse?.messages || []), userMessage];
    onUpdateConversation(convToUse!.id, newMessages);
    setInput('');
    setIsLoading(true);
    setPromptSent(true);

    try {
      const controller = new AbortController();
      const response = await fetch(
        'http://localhost:8000/api/chat/completions',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session?.accessToken || ''}`,
          },
          body: JSON.stringify({
            query: userMessage.content,
            user_id: session?.user.id,
            session_id: convToUse!.id,
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
                  onUpdateConversation(convToUse!.id, [...newMessages, aiMessage]);
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
    console.log('Copied to clipboard!');
  };

  const handleQuickPrompt = async (prompt: string) => {
    setInput('');
    setPromptSent(true);
    if (onSendPrompt) {
      setIsLoading(true);
      await onSendPrompt(prompt);
      setIsLoading(false);
    }
  };

  const handleLike = useCallback((messageId: string) => {
    setLikedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
        setDislikedMessages(prevDisliked => {
          const newDisliked = new Set(prevDisliked);
          newDisliked.delete(messageId);
          return newDisliked;
        });
      }
      return newSet;
    });
  }, []);

  const handleDislike = useCallback((messageId: string) => {
    setDislikedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
        setLikedMessages(prevLiked => {
          const newLiked = new Set(prevLiked);
          newLiked.delete(messageId);
          return newLiked;
        });
      }
      return newSet;
    });
  }, []);

  // REVISED handleReset FUNCTION
  const handleReset = useCallback((aiMessageToRegenerate: Message) => {
    if (!conversation || !aiMessageToRegenerate) return;

    // Find the index of the AI message that needs to be regenerated
    const aiMessageIndex = conversation.messages.findIndex(
      (msg) => msg.id === aiMessageToRegenerate.id && msg.role === 'assistant'
    );

    if (aiMessageIndex === -1) {
      console.warn("AI message to regenerate not found in current conversation.");
      return;
    }

    // Find the immediate preceding user message
    let precedingUserMessage: Message | undefined;
    for (let i = aiMessageIndex - 1; i >= 0; i--) {
      if (conversation.messages[i].role === 'user') {
        precedingUserMessage = conversation.messages[i];
        break;
      }
    }

    if (!precedingUserMessage) {
      console.warn("No preceding user message found to regenerate from.");
      // You might want to provide user feedback here if a response can't be regenerated.
      return;
    }

    // Remove the AI message and any subsequent messages (if any were streamed after it)
    const messagesBeforeRegeneration = conversation.messages.slice(0, aiMessageIndex);
    onUpdateConversation(conversation.id, messagesBeforeRegeneration);

    // Re-send the content of the identified preceding user message
    handleSendMessage(precedingUserMessage.content);

  }, [conversation, onUpdateConversation, handleSendMessage]);


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
              onClick={() => !promptSent && handleQuickPrompt(prompt.label)}
              className={`flex items-center gap-3 p-4 border rounded-xl bg-muted/30 transition min-h-[80px] min-w-[320px] ${
                promptSent ? 'cursor-not-allowed opacity-50' : 'cursor-pointer hover:bg-muted'
              }`}
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

  const shouldShowWelcomeContent = !conversation || conversation.messages.length === 0;

  return (
    <div className="flex-1 flex flex-col gradient-aurora">
      <NavModeToggle />

      {/* Main content area (messages or welcome screen) */}
      <ScrollArea className="flex-1 p-6 pt-24" ref={scrollAreaRef}>
        <div className="max-w-4xl mx-auto space-y-6">
          {shouldShowWelcomeContent && !promptSent ? (
            <div className="text-center">
              <div className="p-6 rounded-full bg-primary/10 mx-auto mb-4 w-fit">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Welcome to MediChat A.I+</h2>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Welcome to MediChat AI-powered chatbot designed to provide reliable medical information about patients.
              </p>
              <QuickPrompts />
            </div>
          ) : (
            <>
              {conversation?.messages.map((message) => (
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
                    className={`message-bubble group rounded-lg p-4 max-w-2xl ${
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
                          {/* ThumbsUp Button */}
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-8 w-8 p-0 ${likedMessages.has(message.id) ? 'text-green-500' : ''}`}
                            onClick={() => handleLike(message.id)}
                            title={likedMessages.has(message.id) ? 'Unlike' : 'Like'}
                          >
                            <ThumbsUp className="h-3 w-3" />
                          </Button>
                          {/* ThumbsDown Button */}
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-8 w-8 p-0 ${dislikedMessages.has(message.id) ? 'text-red-500' : ''}`}
                            onClick={() => handleDislike(message.id)}
                            title={dislikedMessages.has(message.id) ? 'Undislike' : 'Dislike'}
                          >
                            <ThumbsDown className="h-3 w-3" />
                          </Button>
                          {/* Copy Button */}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => copyToClipboard(message.content)}
                            title="Copy"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                          {/* Reset/Regenerate Button */}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => handleReset(message)}
                            title="Regenerate response"
                            disabled={isLoading}
                          >
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
            </>
          )}
        </div>
      </ScrollArea>

      {/* Input box - this section is now ALWAYS rendered */}
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