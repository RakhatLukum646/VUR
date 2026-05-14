import { useRef, useEffect, useCallback } from 'react';
import { Camera } from '../components/Camera';
import type { CameraRef } from '../components/Camera';
import { TranslationPanel } from '../components/TranslationPanel';
import { Controls } from '../components/Controls';
import { StatusBar } from '../components/StatusBar';
import { ToastContainer } from '../components/Toast';
import { useWebSocket } from '../hooks/useWebSocket';
import { useToast } from '../hooks/useToast';
import { useAppStore } from '../store/useAppStore';
import { translateSigns, clearSession as clearSessionApi } from '../services/api';
import '../App.css';

export default function TranslatorPage() {
  const cameraRef = useRef<CameraRef>(null);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const accumulatedSignsRef = useRef<string[]>([]);
  const wsRef = useRef<ReturnType<typeof useWebSocket> | null>(null);

  const { toasts, dismiss, toast } = useToast();

  const ws = useWebSocket();

  useEffect(() => {
    wsRef.current = ws;
  }, [ws]);

  const {
    connect,
    disconnect,
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
    isCapturing,
    sendCommand,
    error: wsError,
  } = ws;

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
    clearDetectedSigns,
    setCurrentSentence,
    clearSession: clearStore,
    addToHistory,
  } = useAppStore();

  useEffect(() => {
    if (!isTranslating) return;
    sendCommand('start');
  }, [isTranslating, language, sendCommand]);

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
        clearDetectedSigns();

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
  }, [lastMessage, addDetectedSign, setCurrentSentence, addToHistory, toast, clearDetectedSigns]);

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
      }, 100);
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
      clearDetectedSigns();
    } catch (err) {
      console.error('Translation failed:', err);
      const msg = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Translation failed', msg);

      const rawFallback = signs.join(' ');
      setCurrentSentence(rawFallback);
      addToHistory({ signs: [...signs], translation: rawFallback, timestamp: Date.now() });
      accumulatedSignsRef.current = [];
      clearDetectedSigns();
    }
  }, [sessionId, language, setCurrentSentence, addToHistory, toast, clearDetectedSigns]);

  useEffect(() => {
    return () => {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return (
    <>
      <ToastContainer toasts={toasts} onDismiss={dismiss} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white/80 dark:bg-gray-900/70 backdrop-blur rounded-2xl border border-gray-200/70 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Camera
                  ref={cameraRef}
                  isTranslating={isTranslating}
                  landmarks={lastLandmarks}
                />

                {detectedSigns.length > 0 && (
                  <button
                    type="button"
                    onClick={handleProcessTranslation}
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors shadow-md"
                  >
                    Translate Signs to Sentence
                  </button>
                )}

                <Controls
                  onStart={handleStart}
                  onStop={handleStop}
                  onClear={handleClear}
                  variant="embedded"
                />
              </div>

              <TranslationPanel
                lastSign={lastSign}
                confidence={lastConfidence}
                guidance={lastGuidance}
                frameQuality={lastFrameQuality}
                stability={lastStability}
                sequenceLength={sequenceLength}
                handDetected={handDetected}
                isCapturing={isCapturing}
              />
            </div>
          </div>

          <div className="h-px bg-gray-200/70 dark:bg-gray-700" />

          <div className="p-6">
            <StatusBar
              detectionGuidance={lastGuidance}
              frameQuality={lastFrameQuality}
              variant="embedded"
            />
          </div>
        </div>

        <div className="mt-8 bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            How to Use
          </h3>
          <ol className="space-y-2 text-blue-800 dark:text-blue-200">
            <li className="flex items-start gap-2">
              <span className="font-bold">1.</span>
              <span>Allow camera access when prompted</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">2.</span>
              <span>Click &quot;Start Translation&quot; to begin</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">3.</span>
              <span>
                Keep one hand centered, well lit, and large enough in the frame
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">4.</span>
              <span>
                Perform RSL gestures — the model captures 32 frames (~1 second) per word, then recognises it automatically
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">5.</span>
              <span>
                Click &quot;Translate Signs to Sentence&quot; to get a grammatically
                correct translation via Gemini
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">6.</span>
              <span>Click &quot;Clear&quot; to start a new session</span>
            </li>
          </ol>
          <p className="mt-4 text-sm text-blue-900 dark:text-blue-200">
            Privacy note: camera frames are processed for live recognition and are
            not stored by the frontend.
          </p>
        </div>
      </main>

      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500 dark:text-gray-400">
            <p>AITU Diploma Project &bull; Team: Ulzhan, Vlad, Rakhat</p>
            <p>
              Session ID: <span className="font-mono">{sessionId}</span>
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}
