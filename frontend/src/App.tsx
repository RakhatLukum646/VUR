import { useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCircle, LogOut } from 'lucide-react';
import { useAuthStore } from './store/useAuthStore';
import { Hand, Github, BookOpen } from 'lucide-react';
import { Camera } from './components/Camera';
import type { CameraRef } from './components/Camera';
import { TranslationPanel } from './components/TranslationPanel';
import { Controls } from './components/Controls';
import { StatusBar } from './components/StatusBar';
import { ToastContainer } from './components/Toast';
import { useWebSocket } from './hooks/useWebSocket';
import { useToast } from './hooks/useToast';
import { useAppStore } from './store/useAppStore';
import { translateSigns, clearSession as clearSessionApi } from './services/api';
import { logoutUser } from './services/authApi';
import './App.css';

function App() {
  const cameraRef = useRef<CameraRef>(null);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const accumulatedSignsRef = useRef<string[]>([]);
  const wsRef = useRef<ReturnType<typeof useWebSocket> | null>(null);


  const { toasts, dismiss, toast } = useToast();

  const ws = useWebSocket();

  useEffect(() => {
    wsRef.current = ws;
  });

  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // Clear local auth state even if the backend session is already gone.
    }
    logout();
    navigate('/login');
  };

  const {
    connect,
    disconnect,
    clearDetection,
    lastMessage,
    lastSign,
    lastConfidence,
    lastLandmarks,
    sendCommand,
    error: wsError,
  } = ws;

  // Surface WebSocket connection errors as toasts
  useEffect(() => {
    if (wsError) {
      toast.error('Connection failed', wsError);
    }
  }, [wsError, toast]);

  const {
    isTranslating,
    sessionId,
    detectedSigns,
    language,
    startTranslation,
    stopTranslation,
    addDetectedSign,
    setCurrentSentence,
    clearSession: clearStore,
    addToHistory,
  } = useAppStore();

  // Handle incoming WebSocket messages (detection + translation)
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === 'detection') {
      const { sign } = lastMessage.payload;

      if (sign) {
        const lastAdded =
          accumulatedSignsRef.current[accumulatedSignsRef.current.length - 1];
        if (sign !== lastAdded) {
          accumulatedSignsRef.current.push(sign);
          addDetectedSign(sign);
        }
      }
    }

    if (lastMessage.type === 'translation') {
      const { translation, signs, fallback } = lastMessage.payload;
      if (translation) {
        setCurrentSentence(translation);
        addToHistory({
          signs: signs || [...accumulatedSignsRef.current],
          translation,
          timestamp: Date.now(),
        });
        accumulatedSignsRef.current = [];

        if (fallback) {
          toast.warning(
            'Offline mode',
            'Gemini API unavailable — showing raw sign sequence as fallback.'
          );
        }
      }
    }

    if (lastMessage.type === 'error') {
      const { message } = lastMessage.payload;
      toast.error('Service error', message || 'An unexpected error occurred.');
    }
  }, [lastMessage, addDetectedSign, setCurrentSentence, addToHistory, toast]);

  const handleStart = useCallback(() => {
    startTranslation();
    connect();
    toast.info('Translation started', 'Make sign gestures in front of the camera.');

    if (cameraRef.current) {
      frameIntervalRef.current = setInterval(() => {
        const frame = cameraRef.current?.captureFrame();
        if (frame) {
          wsRef.current?.sendFrame(frame);
        }
      }, 100); // ~10 FPS
    }
  }, [startTranslation, connect, toast]);

  const handleStop = useCallback(() => {
    stopTranslation();
    disconnect();

    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  }, [stopTranslation, disconnect]);

  const handleClear = useCallback(async () => {
    try {
      await clearSessionApi(sessionId);
    } catch {
      // Session may not exist on backend yet
    }

    sendCommand('clear');
    clearStore();
    clearDetection();
    accumulatedSignsRef.current = [];
  }, [sessionId, sendCommand, clearStore, clearDetection]);

  const handleProcessTranslation = useCallback(async () => {
    const signs = accumulatedSignsRef.current;
    if (signs.length === 0) {
      toast.warning('No signs detected', 'Make some gestures first before translating.');
      return;
    }

    try {
      const result = await translateSigns(signs, sessionId, undefined, language);
      setCurrentSentence(result.translation);

      addToHistory({
        signs: [...signs],
        translation: result.translation,
        timestamp: Date.now(),
      });

      if (result.fallback) {
        toast.warning(
          'Offline mode',
          'Gemini API unavailable — showing raw sign sequence as fallback.'
        );
      } else {
        toast.success('Translation complete');
      }

      accumulatedSignsRef.current = [];
    } catch (err) {
      console.error('Translation failed:', err);
      const msg = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Translation failed', msg);

      // Fallback: show raw signs as the "translation"
      const rawFallback = signs.join(' ');
      setCurrentSentence(rawFallback);
      addToHistory({ signs: [...signs], translation: rawFallback, timestamp: Date.now() });
      accumulatedSignsRef.current = [];
    }
  }, [sessionId, language, setCurrentSentence, addToHistory, toast]);

  useEffect(() => {
    return () => {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return (
    <div className="min-h-screen bg-gray-50">
      <ToastContainer toasts={toasts} onDismiss={dismiss} />

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Hand className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  AI Sign Language Translator
                </h1>
                <p className="text-sm text-gray-500">
                  Real-time sign language to text translation
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <a
                href="https://github.com/rakhatdiploma/iitudiplomas"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <Github className="w-5 h-5" />
                <span className="hidden sm:inline">GitHub</span>
              </a>

              <a
                href="/docs"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <BookOpen className="w-5 h-5" />
                <span className="hidden sm:inline">Docs</span>
              </a>

              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <UserCircle className="w-5 h-5 text-blue-600" />
                <span className="hidden md:inline text-sm text-gray-700">
                  {user?.name || 'Profile'}
                </span>
              </button>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 hover:bg-red-50 hover:border-red-200 transition-colors text-gray-700 hover:text-red-600"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden md:inline text-sm">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <StatusBar />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="space-y-4">
            <Camera ref={cameraRef} isTranslating={isTranslating} landmarks={lastLandmarks} />

            {detectedSigns.length > 0 && (
              <button
                onClick={handleProcessTranslation}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors shadow-md"
              >
                Translate Signs to Sentence
              </button>
            )}
          </div>

          <TranslationPanel
            lastSign={lastSign}
            confidence={lastConfidence}
          />
        </div>

        <Controls
          onStart={handleStart}
          onStop={handleStop}
          onClear={handleClear}
        />

        <div className="mt-8 bg-blue-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            How to Use
          </h3>
          <ol className="space-y-2 text-blue-800">
            <li className="flex items-start gap-2">
              <span className="font-bold">1.</span>
              <span>Allow camera access when prompted</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">2.</span>
              <span>Click "Start Translation" to begin</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">3.</span>
              <span>Make sign language gestures in front of the camera</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">4.</span>
              <span>
                Click "Translate Signs to Sentence" to get a grammatically
                correct translation via Gemini
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">5.</span>
              <span>Click "Clear" to start a new session</span>
            </li>
          </ol>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <p>AITU Diploma Project &bull; Team: Ulzhan, Vlad, Rakhat</p>
            <p>
              Session ID: <span className="font-mono">{sessionId}</span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
