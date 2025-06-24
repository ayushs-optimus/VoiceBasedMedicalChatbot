'use client';

import { useState, useEffect, useCallback } from 'react';
import { VoiceControls } from './voice-controls';
import { TranscriptionSidebar } from './transcription-sidebar';
import { VoiceChatArea } from './voice-chat-area';
import { useWebSocket } from '@/hooks/use-websocket';
import { useVoiceRecognition } from '@/hooks/use-voice-recognition';
import { TranscriptionEntry, VoiceMessage } from '@/types/voice';
import { useSession } from '@/hooks/use-session';

export function VoiceChatInterface() {
  const { session } = useSession(); // ✅ call hook at the top level
  const userRoles = session?.user?.roles ?? [];
  const [transcriptions, setTranscriptions] = useState<TranscriptionEntry[]>([]);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState('');
  const [sessionId] = useState(() => `voice-session-${Date.now()}`);

  // Connect to your backend WebSocket endpoint
  const { 
    isConnected, 
    sendMessage, 
    lastMessage 
  } = useWebSocket(`/voice/ws/${sessionId}`, {
    onOpen: () => {
      console.log('Voice WebSocket connected');
      sendMessage({
        type: 'ping',
        data: { session_id: sessionId }
      });
    },
    onClose: () => {
      console.log('Voice WebSocket disconnected');
    },
    onError: (error) => {
      console.error('Voice WebSocket error:', error);
    }
  });

  const handleVoiceResult = useCallback((transcript: string, isFinal: boolean) => {
    console.log('Voice result:', { transcript, isFinal });
    
    // Show interim results
    if (!isFinal) {
      setCurrentTranscription(transcript);
      return;
    }
    
    // Process final results
    if (isFinal && transcript.trim()) {
      const transcriptId = `transcript-${Date.now()}`;
      
      // Add transcription entry
      const newTranscription: TranscriptionEntry = {
        id: transcriptId,
        text: transcript,
        timestamp: new Date(),
        confidence: 0.95,
        isFinal: true
      };
      
      setTranscriptions(prev => [...prev, newTranscription]);
      
      // Add user message
      const userMessage: VoiceMessage = {
        id: `msg-${transcriptId}`,
        content: transcript,
        role: 'user',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, userMessage]);
      // Send to backend
      if (isConnected) {
        sendMessage({
          type: 'transcription',
          data: {
            text: transcript,
            timestamp: new Date().toISOString(),
            isFinal: true,
            confidence: 0.95,
            session_id: sessionId,
            user_roles: userRoles
          }
        });
      }
      
      // Clear current transcription
      setCurrentTranscription('');
    }
  }, [isConnected, sendMessage, sessionId]);

  const handleVoiceError = useCallback((error: any) => {
    console.error('Voice recognition error:', error);
    setIsRecording(false);
    setCurrentTranscription('');
  }, []);

  // Voice recognition hook
  const {
    startListening,
    stopListening,
    transcript,
    isListening,
    resetTranscript,
    isSupported,
    interimTranscript
  } = useVoiceRecognition({
    onResult: handleVoiceResult,
    onError: handleVoiceError,
    continuous: true,
    interimResults: true,
    language: 'en-US'
  });

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const message = JSON.parse(lastMessage.data);
        console.log('Received backend message:', message);
        
        if (message.type === 'ai_response') {
          const newMessage: VoiceMessage = {
            id: `ai-${Date.now()}`,
            content: message.data.text,
            role: 'assistant',
            timestamp: new Date(),
            audioUrl: message.data.audio_url
          };
          setMessages(prev => [...prev, newMessage]);
        } else if (message.type === 'error') {
          console.error('Backend error:', message.data.message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  const handleStartRecording = useCallback(() => {
    if (!isSupported) {
      handleVoiceError('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }
    
    if (!isConnected) {
      handleVoiceError('Not connected to server. Please check your internet connection.');
      return;
    }
    
    console.log('Starting recording...');
    setIsRecording(true);
    setCurrentTranscription('');
    
    const success = startListening();
    if (!success) {
      setIsRecording(false);
    }
  }, [isSupported, isConnected, startListening, handleVoiceError]);

  const handleStopRecording = useCallback(() => {
    console.log('Stopping recording...');
    setIsRecording(false);
    stopListening();
    setCurrentTranscription('');
  }, [stopListening]);

  const clearTranscriptions = useCallback(() => {
    setTranscriptions([]);
    setMessages([]);
    resetTranscript();
    setCurrentTranscription('');
  }, [resetTranscript]);

  // Auto-stop if disconnected
  useEffect(() => {
    if (!isConnected && isRecording) {
      console.log('WebSocket disconnected, stopping recording');
      handleStopRecording();
    }
  }, [isConnected, isRecording, handleStopRecording]);

  // Show support warning
  useEffect(() => {
    if (!isSupported) {
      console.warn('Speech recognition not supported. Please use Chrome, Edge, or Safari.');
    }
  }, [isSupported]);

  return (
    <div className="flex h-screen bg-background">
      <TranscriptionSidebar
        transcriptions={transcriptions}
        currentTranscription={currentTranscription}
        isConnected={isConnected}
        onClear={clearTranscriptions}
      />
      <div className="flex-1 flex flex-col">
        <VoiceChatArea
          messages={messages}
          isRecording={isRecording}
          isConnected={isConnected}
        />
        <VoiceControls
          isRecording={isRecording}
          isListening={isListening}
          isConnected={isConnected}
          isSupported={isSupported}
          onStartRecording={handleStartRecording}
          onStopRecording={handleStopRecording}
          currentTranscription={currentTranscription}
        />
      </div>
    </div>
  );
}