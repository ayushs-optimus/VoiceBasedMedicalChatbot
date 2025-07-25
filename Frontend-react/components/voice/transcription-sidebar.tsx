'use client';

import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { TranscriptionEntry } from '@/types/voice';
import { 
  Trash2, 
  Clock, 
  Mic,
  Bot,
  Wifi,
  WifiOff,
  AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';

interface TranscriptionSidebarProps {
  transcriptions: TranscriptionEntry[];
  currentTranscription: string;
  isConnected: boolean;
  onClear: () => void;
}

export function TranscriptionSidebar({
  transcriptions,
  currentTranscription,
  isConnected,
  onClear
}: TranscriptionSidebarProps) {
  return (
    <div className="w-80 bg-card border-r border-border gradient-aurora-sidebar flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">MediChat A.I+</h1>
        </div>
        
        <div className="flex items-center justify-between">
          <Badge variant={isConnected ? "default" : "destructive"} className="flex items-center gap-1">
            {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          
          <Button
            onClick={onClear}
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-destructive"
            disabled={transcriptions.length === 0}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Connection Warning */}
        {!isConnected && (
          <div className="mt-3 p-2 bg-destructive/10 border border-destructive/20 rounded-md">
            <div className="flex items-center gap-2 text-destructive text-xs">
              <AlertCircle className="h-3 w-3" />
              <span>Backend connection lost. Trying to reconnect...</span>
            </div>
          </div>
        )}
      </div>

      {/* Real-time Transcription */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-2">
          <Mic className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Live Transcription</span>
        </div>
        
        <Card className="p-3 min-h-[60px] bg-muted/30">
          {currentTranscription ? (
            <p className="text-sm text-foreground">{currentTranscription}</p>
          ) : (
            <p className="text-sm text-muted-foreground italic">
              {isConnected 
                ? "Start speaking to see live transcription..." 
                : "Connect to backend to start transcription..."
              }
            </p>
          )}
        </Card>
      </div>

      {/* Transcription History */}
      <div className="flex-1 overflow-hidden">
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-muted-foreground">Transcription History</span>
            <Badge variant="secondary" className="text-xs">
              {transcriptions.length}
            </Badge>
          </div>
        </div>
        
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-3">
            {transcriptions.length === 0 ? (
              <div className="text-center py-8">
                <Mic className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  No transcriptions yet
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {isConnected 
                    ? "Start recording to see transcriptions here" 
                    : "Connect to backend first"
                  }
                </p>
              </div>
            ) : (
              transcriptions.map((transcription) => (
                <Card key={transcription.id} className="p-3 hover:bg-muted/50 transition-colors">
                  <div className="flex items-start gap-2 mb-2">
                    <Mic className="h-3 w-3 text-primary mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm break-words">{transcription.text}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {format(transcription.timestamp, 'HH:mm:ss')}
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {Math.round(transcription.confidence * 100)}%
                    </Badge>
                  </div>
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Stats */}
      <div className="p-4 border-t border-border">
        <div className="grid grid-cols-2 gap-2 text-center">
          <div>
            <p className="text-lg font-bold text-primary">{transcriptions.length}</p>
            <p className="text-xs text-muted-foreground">Transcriptions</p>
          </div>
          <div>
            <p className="text-lg font-bold text-primary">
              {transcriptions.reduce((acc, t) => acc + t.text.split(' ').length, 0)}
            </p>
            <p className="text-xs text-muted-foreground">Words</p>
          </div>
        </div>
      </div>
    </div>
  );
}