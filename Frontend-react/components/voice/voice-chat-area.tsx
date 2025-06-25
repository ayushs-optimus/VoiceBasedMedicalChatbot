'use client';

import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { VoiceMessage } from '@/types/voice';
import { useSession } from '@/hooks/use-session';
import {
  Bot,
  Mic,
  Play,
  Pause,
  Volume2,
  Sparkles
} from 'lucide-react';
import { format } from 'date-fns';
import { useState } from 'react';


interface VoiceChatAreaProps {
  messages: VoiceMessage[];
  isRecording: boolean;
  isConnected: boolean;
}

export function VoiceChatArea({
  messages,
  isRecording,
  isConnected
}: VoiceChatAreaProps) {
  const { session } = useSession();
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);

  const playAudio = (audioUrl: string, messageId: string) => {
    setPlayingAudio(messageId);
    setTimeout(() => {
      setPlayingAudio(null);
    }, 3000);
  };

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gradient-aurora">
        <div className="text-center">
          <div className="rounded-full bg-primary/10 mx-auto mb-4 w-fit">
            <Sparkles className="h-12 w-12 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Voice Chat Ready</h2>
          <p className="text-muted-foreground mb-2 max-w-md">
            Start speaking to begin your voice conversation with AI. Your speech will be transcribed in real-time.
          </p>
          <div className="flex items-center justify-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-muted-foreground">
              {isConnected ? 'Connected and ready' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col gradient-aurora">
      <ScrollArea className="flex-1 p-6 pt-24">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
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

              <Card className={`p-4 max-w-2xl ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-card border border-border'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                    {message.role === 'assistant' && message.audioUrl && (
                      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => playAudio(message.audioUrl!, message.id)}
                          disabled={playingAudio === message.id}
                        >
                          {playingAudio === message.id ? (
                            <>
                              <Pause className="h-4 w-4 mr-2" /> Playing...
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4 mr-2" /> Play Response
                            </>
                          )}
                        </Button>
                        <Volume2 className="h-4 w-4 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/20">
                  <div className="flex items-center gap-1">
                    {message.role === 'user' ? (
                      <Mic className="h-3 w-3" />
                    ) : (
                      <Bot className="h-3 w-3" />
                    )}
                    <span className="text-xs opacity-70">
                      {format(message.timestamp, 'HH:mm:ss')}
                    </span>
                  </div>
                </div>
              </Card>

              {message.role === 'user' && (
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarImage src={session?.user?.avatar} alt={session?.user?.name} />
                  <AvatarFallback>{session?.user?.name?.[0]}</AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}

          {isRecording && (
            <div className="flex gap-4 justify-end">
              <Card className="bg-primary/10 border-primary/20 p-4 max-w-2xl">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-destructive rounded-full animate-pulse"></div>
                  <span className="text-sm text-muted-foreground">Recording...</span>
                </div>
              </Card>
              <Avatar className="h-8 w-8 flex-shrink-0">
                <AvatarImage src={session?.user?.avatar} alt={session?.user?.name} />
                <AvatarFallback>{session?.user?.name?.[0]}</AvatarFallback>
              </Avatar>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
