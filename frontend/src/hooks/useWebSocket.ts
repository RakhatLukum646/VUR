import { useState, useCallback, useRef, useEffect } from 'react';
import type { UseWebSocketReturn, DetectionResult, FrameMessage, CommandMessage } from '../types';
import { useAppStore } from '../store/useAppStore';

const WS_URL = 'ws://localhost:8001/ws/sign-detection';

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  const [lastMessage, setLastMessage] = useState<DetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const { sessionId, setConnected, setConnectionStatus } = useAppStore();

  const connect = useCallback(() => {
    try {
      setError(null);
      setConnectionStatus('connecting');

      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setConnectionStatus('connected');
        
        const startMessage: CommandMessage = {
          type: 'command',
          payload: {
            action: 'start',
            session_id: sessionId,
          },
        };
        ws.send(JSON.stringify(startMessage));
      };

      ws.onmessage = (event) => {
        try {
          const data: DetectionResult = JSON.parse(event.data);
          setLastMessage(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;
        
        // Clear frame interval
        if (frameIntervalRef.current) {
          clearInterval(frameIntervalRef.current);
          frameIntervalRef.current = null;
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setError('Failed to connect to WebSocket');
      setConnectionStatus('error');
    }
  }, [sessionId, setConnected, setConnectionStatus]);

  const disconnect = useCallback(() => {
    // Send stop command
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const stopMessage: CommandMessage = {
        type: 'command',
        payload: {
          action: 'stop',
          session_id: sessionId,
        },
      };
      wsRef.current.send(JSON.stringify(stopMessage));
    }

    // Clear frame interval
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
    setConnectionStatus('disconnected');
  }, [sessionId, setConnected, setConnectionStatus]);

  const sendFrame = useCallback((image: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message: FrameMessage = {
        type: 'frame',
        payload: {
          image,
          timestamp: Date.now(),
          session_id: sessionId,
        },
      };
      wsRef.current.send(JSON.stringify(message));
    }
  }, [sessionId]);

  const sendCommand = useCallback((action: 'start' | 'stop' | 'clear') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message: CommandMessage = {
        type: 'command',
        payload: {
          action,
          session_id: sessionId,
        },
      };
      wsRef.current.send(JSON.stringify(message));
    }
  }, [sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected: useAppStore((state) => state.isConnected),
    connect,
    disconnect,
    sendFrame,
    sendCommand,
    lastMessage,
    error,
  };
}
