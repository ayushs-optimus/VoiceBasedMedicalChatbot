'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface UseVoiceRecognitionOptions {
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: any) => void;
  continuous?: boolean;
  interimResults?: boolean;
  language?: string;
}

export function useVoiceRecognition(options: UseVoiceRecognitionOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  
  const {
    onResult,
    onError,
    continuous = true,
    interimResults = true,
    language = 'en-US'
  } = options;

  const recognitionRef = useRef<any>(null);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        setIsSupported(true);
        console.log('Speech recognition is supported');
      } else {
        setIsSupported(false);
        console.warn('Speech recognition not supported in this browser');
      }
    }
  }, []);

  const startListening = useCallback(() => {
    if (!isSupported) {
      const errorMsg = 'Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari.';
      onError?.(errorMsg);
      return false;
    }

    if (isListening) {
      console.log('Already listening...');
      return true;
    }

    try {
      console.log('Starting speech recognition...');
      
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      // Simple configuration
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        console.log('Speech recognition started');
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        console.log('Recognition result event:', event);
        
        // Get the latest result
        const lastResult = event.results[event.results.length - 1];
        const transcript = lastResult[0].transcript.trim();
        const isFinal = lastResult.isFinal;
        
        console.log('Transcript:', transcript, 'isFinal:', isFinal);
        
        if (transcript) {
          setTranscript(transcript);
          
          if (isFinal) {
            setFinalTranscript(transcript);
            setInterimTranscript('');
            onResult?.(transcript, true);
          } else if (interimResults) {
            setInterimTranscript(transcript);
            onResult?.(transcript, false);
          }
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        
        if (event.error !== 'aborted') {
          onError?.(event.error);
        }
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
        
        // Auto-restart if continuous
        if (continuous && recognitionRef.current) {
          setTimeout(() => {
            if (recognitionRef.current && !isListening) {
              console.log('Auto-restarting recognition...');
              try {
                recognitionRef.current.start();
              } catch (error) {
                console.error('Error restarting recognition:', error);
              }
            }
          }, 1000);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
      
      return true;
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      onError?.(error);
      return false;
    }
  }, [isSupported, isListening, continuous, interimResults, language, onResult, onError]);

  const stopListening = useCallback(() => {
    console.log('Stopping speech recognition...');
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      } catch (error) {
        console.error('Error stopping recognition:', error);
      }
    }
    
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    console.log('Resetting transcripts...');
    setTranscript('');
    setInterimTranscript('');
    setFinalTranscript('');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          // Ignore cleanup errors
        }
      }
    };
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    finalTranscript,
    isSupported,
    startListening,
    stopListening,
    resetTranscript
  };
}