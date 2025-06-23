'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Mic, 
  MicOff, 
  Wifi, 
  WifiOff,
  Volume2,
  AlertTriangle
} from 'lucide-react';

interface VoiceControlsProps {
  isRecording: boolean;
  isListening: boolean;
  isConnected: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  currentTranscription: string;
}

export function VoiceControls({
  isRecording,
  isListening,
  isConnected,
  onStartRecording,
  onStopRecording,
  currentTranscription
}: VoiceControlsProps) {
  return (
    <div className="border-t border-border p-6 bg-card/50 backdrop-blur-sm">
      <div className="max-w-4xl mx-auto">
        {/* Connection Status */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Badge variant={isConnected ? "default" : "destructive"} className="flex items-center gap-1">
              {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
              {isConnected ? 'Backend Connected' : 'Backend Disconnected'}
            </Badge>
            {isListening && (
              <Badge variant="secondary" className="flex items-center gap-1">
                <Volume2 className="h-3 w-3" />
                Listening...
              </Badge>
            )}
          </div>
        </div>

        {/* Connection Warning */}
        {!isConnected && (
          <Card className="p-3 mb-4 bg-destructive/10 border-destructive/20">
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertTriangle className="h-4 w-4" />
              <div>
                <p className="font-medium">Backend Connection Lost</p>
                <p className="text-xs">Make sure your Python FastAPI backend is running on port 8000</p>
              </div>
            </div>
          </Card>
        )}

        {/* Current Transcription Preview */}
        {currentTranscription && (
          <Card className="p-3 mb-4 bg-muted/50">
            <p className="text-sm text-muted-foreground mb-1">Current transcription:</p>
            <p className="text-sm">{currentTranscription}</p>
          </Card>
        )}

        {/* Voice Controls */}
        <div className="flex items-center justify-center gap-4">
          <Button
            onClick={isRecording ? onStopRecording : onStartRecording}
            disabled={!isConnected}
            size="lg"
            className={`h-16 w-16 rounded-full transition-all duration-200 ${
              isRecording 
                ? 'bg-destructive hover:bg-destructive/90 animate-pulse' 
                : 'bg-primary hover:bg-primary/90'
            }`}
          >
            {isRecording ? (
              <MicOff className="h-6 w-6" />
            ) : (
              <Mic className="h-6 w-6" />
            )}
          </Button>
          
          <div className="text-center">
            <p className="text-sm font-medium">
              {!isConnected 
                ? 'Connect to backend first' 
                : isRecording 
                  ? 'Recording... Click to stop' 
                  : 'Click to start recording'
              }
            </p>
            <p className="text-xs text-muted-foreground">
              {isConnected 
                ? 'Ready to transcribe and send to AI' 
                : 'Start your Python FastAPI backend'
              }
            </p>
          </div>
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <div className="flex items-center justify-center mt-4">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-destructive rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-destructive rounded-full animate-bounce delay-75"></div>
              <div className="w-2 h-2 bg-destructive rounded-full animate-bounce delay-150"></div>
            </div>
          </div>
        )}

        {/* Backend Instructions */}
        {!isConnected && (
          <div className="mt-4 text-center">
            <p className="text-xs text-muted-foreground">
              To start voice chat, run your Python backend:
            </p>
            <code className="text-xs bg-muted px-2 py-1 rounded mt-1 inline-block">
              cd backend && python run.py
            </code>
          </div>
        )}
      </div>
    </div>
  );
}