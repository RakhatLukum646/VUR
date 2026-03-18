// Normalized landmark point [x, y] relative to wrist, unit-scaled
export type Landmark = [number, number];

// WebSocket message from backend
export interface DetectionResult {
  type: 'detection' | 'translation' | 'error' | 'command';
  payload: {
    sign?: string | null;
    confidence?: number;
    hand_detected?: boolean;
    landmarks?: Landmark[];
    timestamp?: number;
    status?: string;
    session_id?: string;
    message?: string;
    translation?: string;
    signs?: string[];
    processing_time_ms?: number;
    fallback?: boolean;
    language?: string;
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
    language?: string;
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

export type Language = 'en' | 'ru' | 'kz';

export const LANGUAGE_OPTIONS: { value: Language; label: string; flag: string }[] = [
  { value: 'en', label: 'English', flag: '🇬🇧' },
  { value: 'ru', label: 'Russian', flag: '🇷🇺' },
  { value: 'kz', label: 'Kazakh', flag: '🇰🇿' },
];

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
  language: Language;
  
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
  setLanguage: (language: Language) => void;
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
  clearDetection: () => void;
  lastMessage: DetectionResult | null;
  lastSign: string | null;
  lastConfidence: number;
  lastLandmarks: Landmark[] | null;
  error: string | null;
}
