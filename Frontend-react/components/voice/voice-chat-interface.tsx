'use client';

import { useState, useEffect } from 'react';
import { VoiceControls } from './voice-controls';
import { TranscriptionSidebar } from './transcription-sidebar';
import { VoiceChatArea } from './voice-chat-area';
import { useWebSocket } from '@/hooks/use-websocket';
import { useVoiceRecognition } from '@/hooks/use-voice-recognition';
import { TranscriptionEntry, VoiceMessage } from '@/types/voice';

export function VoiceChatInterface() {
  const [transcriptions, setTranscriptions] = useState<TranscriptionEntry[]>([]);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState('');
  const [sessionId] = useState(() => `voice-session-${Date.now()}`);

  const {
    isConnected,
    sendMessage,
    lastMessage,
    connectionStatus
  } = useWebSocket(`/voice/ws/${sessionId}`, {
    onOpen: () => {
      console.log('✅ Voice WebSocket connected');
      if (sendMessage) {
        console.log('🔁 Sending initial ping...');
        sendMessage({
          type: 'ping',
          data: { session_id: sessionId }
        });
      } else {
        console.warn('⚠️ sendMessage not available in onOpen');
      }
    },
    onClose: () => {
      console.log('🔌 Voice WebSocket disconnected');
    },
    onError: (error) => {
      console.error('❌ Voice WebSocket error:', error);
    }
  });

  const {
    startListening,
    stopListening,
    transcript,
    isListening,
    resetTranscript
  } = useVoiceRecognition({
    onResult: (transcript: string, isFinal: boolean) => {
      setCurrentTranscription(transcript);

      if (isFinal && transcript.trim()) {
        const newTranscription: TranscriptionEntry = {
          id: Date.now().toString(),
          text: transcript,
          timestamp: new Date(),
          confidence: 0.95,
          isFinal: true
        };
        setTranscriptions(prev => [...prev, newTranscription]);

        const userMessage: VoiceMessage = {
          id: Date.now().toString(),
          content: transcript,
          role: 'user',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);

        console.log('📤 Sending final transcription:', transcript);
        sendMessage({
          type: 'transcription',
          data: {
            text: transcript,
            timestamp: new Date().toISOString(),
            isFinal: true,
            confidence: 0.95,
            session_id: sessionId
          }
        });

        setCurrentTranscription('');
      } else if (!isFinal && transcript.trim()) {
        console.log('📤 Sending interim transcription:', transcript);
        sendMessage({
          type: 'transcription',
          data: {
            text: transcript,
            timestamp: new Date().toISOString(),
            isFinal: false,
            confidence: 0.8,
            session_id: sessionId
          }
        });
      }
    },
    onError: (error) => {
      console.error('🎙️ Voice recognition error:', error);
    }
  });

  // Handle backend WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (!lastMessage.data) {
          console.warn('⚠️ Received empty WebSocket message');
          return;
        }

        const message = JSON.parse(lastMessage.data);
        console.log('📥 Received from backend:', message);

        if (message.type === 'ai_response') {
          const newMessage: VoiceMessage = {
            id: Date.now().toString(),
            content: message.data.text,
            role: 'assistant',
            timestamp: new Date(),
            audioUrl: message.data.audio_url
          };
          setMessages(prev => [...prev, newMessage]);
        } else if (message.type === 'error') {
          console.error('❗ Backend error:', message.data.message);
        } else if (message.type === 'pong') {
          console.log('🔁 Received pong from backend');
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  // Periodic WebSocket connection status logger
  useEffect(() => {
    const interval = setInterval(() => {
      console.log(`[WS] Connected: ${isConnected} | Status: ${connectionStatus}`);
    }, 2000);

    return () => clearInterval(interval);
  }, [isConnected, connectionStatus]);

  const handleStartRecording = () => {
    if (!isConnected) {
      console.warn('⚠️ WebSocket not connected. Cannot start recording.');
      return;
    }
    setIsRecording(true);
    startListening();
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    stopListening();
  };

  const clearTranscriptions = () => {
    setTranscriptions([]);
    setMessages([]);
    resetTranscript();
    setCurrentTranscription('');
  };

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
          onStartRecording={handleStartRecording}
          onStopRecording={handleStopRecording}
          currentTranscription={currentTranscription}
        />
        <div className="p-2">
          {!isConnected && (
            <div className="text-sm text-red-500">WebSocket not connected</div>
          )}
          <button
            onClick={() => {
              console.log('📤 Sending manual ping...');
              sendMessage({
                type: 'ping',
                data: { session_id: sessionId }
              });
            }}
            className="mt-2 px-3 py-1 text-sm bg-blue-600 text-white rounded"
          >
            Send Ping to Backend
          </button>
        </div>
      </div>
    </div>
  );
}
