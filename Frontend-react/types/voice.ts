export interface TranscriptionEntry {
  id: string;
  text: string;
  timestamp: Date;
  confidence: number;
  isFinal: boolean;
}

export interface VoiceMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  audioUrl?: string; // For AI responses with TTS
}

export interface WebSocketMessage {
  type: 'transcription' | 'ai_response' | 'error';
  data: any;
}

export interface TranscriptionData {
  text: string;
  timestamp: string;
  isFinal: boolean;
  confidence?: number;
}

export interface AIResponseData {
  text: string;
  audioUrl?: string;
  timestamp: string;
}