import { useState, useCallback, useRef, useEffect } from 'react';
import type { UseWebSocketReturn, DetectionResult, FrameMessage, CommandMessage } from '../types';
import { useAppStore } from '../store/useAppStore';
import { useAuthStore } from '../store/useAuthStore';

// In Docker: gateway proxies /ws/ → MediaPipe.
// In local dev set VITE_WS_URL=wss://localhost:8001 in .env.local.
const WS_BASE = import.meta.env.VITE_WS_URL ?? `wss://${window.location.host}`;
const WS_PATH = '/ws/sign-detection';

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [lastMessage, setLastMessage] = useState<DetectionResult | null>(null);
  const [lastSign, setLastSign] = useState<string | null>(null);
  const [lastConfidence, setLastConfidence] = useState(0);
  const [lastLandmarks, setLastLandmarks] = useState<[number, number][] | null>(null);
  const [lastGuidance, setLastGuidance] = useState<string | null>(
    'Show one hand in the frame to start detection.'
  );
  const [lastFrameQuality, setLastFrameQuality] = useState(0);
  const [lastStability, setLastStability] = useState(0);
  const [sequenceLength, setSequenceLength] = useState(0);
  const [handDetected, setHandDetected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { sessionId, language, setConnected, setConnectionStatus } = useAppStore();
  const accessToken = useAuthStore((state) => state.accessToken);

  const connect = useCallback(() => {
    try {
      setError(null);
      setConnectionStatus('connecting');

      const tokenParam = accessToken ? `?token=${encodeURIComponent(accessToken)}` : '';
      const ws = new WebSocket(`${WS_BASE}${WS_PATH}${tokenParam}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setConnectionStatus('connected');
        
        const startMessage: CommandMessage = {
          type: 'command',
          payload: {
            action: 'start',
            session_id: sessionId,
            language,
          },
        };
        ws.send(JSON.stringify(startMessage));
      };

      ws.onmessage = (event) => {
        try {
          const data: DetectionResult = JSON.parse(event.data);
          setLastMessage(data);
          if (data.type === 'detection') {
            const {
              sign,
              confidence,
              hand_detected,
              landmarks,
              guidance,
              frame_quality,
              stability,
              sequence_length,
            } = data.payload;
            setLastSign(sign ?? null);
            setLastConfidence(confidence ?? 0);
            setLastGuidance(guidance ?? null);
            setLastFrameQuality(frame_quality ?? 0);
            setLastStability(stability ?? 0);
            setSequenceLength(sequence_length ?? 0);
            setHandDetected(Boolean(hand_detected));
            if (hand_detected && landmarks) {
              setLastLandmarks(landmarks as [number, number][]);
            } else if (!hand_detected) {
              setLastLandmarks(null);
            }
          }
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
    } catch {
      setError('Failed to connect to WebSocket');
      setConnectionStatus('error');
    }
  }, [sessionId, language, accessToken, setConnected, setConnectionStatus]);

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

  const clearDetection = useCallback(() => {
    setLastSign(null);
    setLastConfidence(0);
    setLastLandmarks(null);
    setLastGuidance('Show one hand in the frame to start detection.');
    setLastFrameQuality(0);
    setLastStability(0);
    setSequenceLength(0);
    setHandDetected(false);
  }, []);

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
    clearDetection,
    lastMessage,
    lastSign,
    lastConfidence,
    lastLandmarks,
    lastGuidance,
    lastFrameQuality,
    lastStability,
    sequenceLength,
    handDetected,
    error,
  };
}
