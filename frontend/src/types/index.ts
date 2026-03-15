// WebSocket message from backend
export interface DetectionResult {
  type: 'detection' | 'translation' | 'error' | 'command';
  payload: {
    sign?: string | null;
    confidence?: number;
    hand_detected?: boolean;
    landmarks?: [number, number][];
    timestamp?: number;
    status?: string;
    session_id?: string;
    message?: string;
    translation?: string;
    signs?: string[];
    processing_time_ms?: number;
    fallback?: boolean;
  };
}

// Frame message to send to backend
export interface FrameMessage {
  type: 'frame';
  payload: {
    image: string;
    timestamp: number;
    session_id: string;
  };
}

// Command message
export interface CommandMessage {
  type: 'command';
  payload: {
    action: 'start' | 'stop' | 'clear';
    session_id: string;
  };
}

// Translation response from LLM service
export interface TranslationResponse {
  translation: string;
  confidence: number;
  session_id: string;
  processing_time_ms: number;
  alternatives?: string[];
  fallback?: boolean;
}

// Session context
export interface SessionContext {
  session_id: string;
  context: string;
  history: Array<{
    signs: string[];
    translation: string;
  }>;
}

// App state
export interface AppState {
  // Connection state
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  
  // Translation state
  isTranslating: boolean;
  sessionId: string;
  detectedSigns: string[];
  currentSentence: string;
  confidence: number;
  
  // History
  translationHistory: Array<{
    signs: string[];
    translation: string;
    timestamp: number;
  }>;
  
  // Actions
  setConnected: (connected: boolean) => void;
  setConnectionStatus: (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;
  startTranslation: () => void;
  stopTranslation: () => void;
  addDetectedSign: (sign: string) => void;
  setCurrentSentence: (sentence: string) => void;
  setConfidence: (confidence: number) => void;
  clearSession: () => void;
  addToHistory: (item: { signs: string[]; translation: string; timestamp: number }) => void;
}

// Camera hook return type
export interface UseCameraReturn {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  isReady: boolean;
  error: string | null;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
  captureFrame: () => string | null;
}

// WebSocket hook return type
export interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendFrame: (image: string) => void;
  sendCommand: (action: 'start' | 'stop' | 'clear') => void;
  lastMessage: DetectionResult | null;
  error: string | null;
}
