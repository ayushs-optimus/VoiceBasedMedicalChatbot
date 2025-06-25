'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

interface UseWebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export function useWebSocket(path: string, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  const {
    onOpen,
    onClose,
    onError,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  // Construct WebSocket URL dynamically at runtime only (browser environment)
  const url = useRef<string | null>(null);
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const host = "localhost:8000"; // Replace with your backend host
      url.current = `${protocol}://${host}${path}`;
      connect();
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);

  const connect = useCallback(() => {
    if (!url.current) {
      console.warn('WebSocket URL not set yet.');
      return;
    }

    if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
      console.warn('WebSocket already connected or connecting.');
      return;
    }

    console.log('Connecting to WebSocket at', url.current);
    setConnectionStatus('connecting');
    ws.current = new WebSocket(url.current);

    ws.current.onopen = () => {
      console.log('WebSocket connected:', url.current);
      setIsConnected(true);
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
      onOpen?.();
    };

    ws.current.onmessage = (event) => {
      setLastMessage(event);
    };

    ws.current.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      onClose?.();

      if (reconnectAttemptsRef.current < reconnectAttempts) {
        reconnectAttemptsRef.current++;
        console.log(`Reconnect attempt ${reconnectAttemptsRef.current}/${reconnectAttempts}`);
        reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
      } else {
        console.warn('Max reconnect attempts reached.');
      }
    };

    ws.current.onerror = (event) => {
      console.error('WebSocket error:', event);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      onError?.(event);
    };
  }, [onOpen, onClose, onError, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const messageString = JSON.stringify(message);
      ws.current.send(messageString);
      return true;
    } else {
      console.warn('WebSocket not open, message not sent:', message);
      return false;
    }
  }, []);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  };
}
