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
import { useUiText } from '../i18n';
import '../App.css';

export default function TranslatorPage() {
  const cameraRef = useRef<CameraRef>(null);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const accumulatedSignsRef = useRef<string[]>([]);
  const wsRef = useRef<ReturnType<typeof useWebSocket> | null>(null);

  const { toasts, dismiss, toast } = useToast();
  const t = useUiText();
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
      toast.error(t.translator.connectionFailed, wsError);
    }
  }, [wsError, toast, t.translator.connectionFailed]);

  const {
    isTranslating,
    sessionId,
    detectedSigns,
    currentSentence,
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
        const lastAdded = accumulatedSignsRef.current[accumulatedSignsRef.current.length - 1];
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
          toast.warning(t.translator.offlineMode, t.translator.offlineDetail);
        }
      }
    }

    if (lastMessage.type === 'error') {
      const { message } = lastMessage.payload;
      toast.error(t.translator.serviceError, message || t.translator.unexpectedError);
    }
  }, [lastMessage, addDetectedSign, setCurrentSentence, addToHistory, toast, clearDetectedSigns, t]);

  const handleStart = useCallback(() => {
    startTranslation();
    connect();
    toast.info(t.translator.translationStarted, t.translator.translationStartedDetail);
    if (cameraRef.current) {
      frameIntervalRef.current = setInterval(() => {
        const frame = cameraRef.current?.captureFrame();
        if (frame) wsRef.current?.sendFrame(frame);
      }, 100);
    }
  }, [startTranslation, connect, toast, t.translator.translationStarted, t.translator.translationStartedDetail]);

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
      // Session may not exist on backend yet.
    }
    sendCommand('clear');
    clearStore();
    clearDetection();
    accumulatedSignsRef.current = [];
  }, [sessionId, sendCommand, clearStore, clearDetection]);

  const handleProcessTranslation = useCallback(async () => {
    const signs = accumulatedSignsRef.current;
    if (signs.length === 0) {
      toast.warning(t.translator.noSigns, t.translator.noSignsDetail);
      return;
    }
    try {
      const result = await translateSigns(signs, sessionId, undefined, language);
      setCurrentSentence(result.translation);
      addToHistory({ signs: [...signs], translation: result.translation, timestamp: Date.now() });
      if (result.fallback) {
        toast.warning(t.translator.offlineMode, t.translator.offlineDetail);
      } else {
        toast.success(t.translator.translationComplete);
      }
      accumulatedSignsRef.current = [];
      clearDetectedSigns();
    } catch (err) {
      console.error('Translation failed:', err);
      const msg = err instanceof Error ? err.message : 'Unknown error';
      toast.error(t.translator.translationFailed, msg);
      const rawFallback = signs.join(' ');
      setCurrentSentence(rawFallback);
      addToHistory({ signs: [...signs], translation: rawFallback, timestamp: Date.now() });
      accumulatedSignsRef.current = [];
      clearDetectedSigns();
    }
  }, [sessionId, language, setCurrentSentence, addToHistory, toast, clearDetectedSigns, t]);

  useEffect(() => {
    return () => {
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
      disconnect();
    };
  }, [disconnect]);

  return (
    <>
      <ToastContainer toasts={toasts} onDismiss={dismiss} />

      {/*
        Single unified layout — responsive classes swap between mobile/desktop.
        Camera is rendered ONCE to avoid double webcam access.
      */}
      <main className="lg:max-w-7xl lg:mx-auto lg:px-8 lg:py-8">

        {/* Outer card shell — only on desktop */}
        <div className="lg:bg-white/80 lg:dark:bg-gray-900/70 lg:backdrop-blur lg:rounded-2xl lg:border lg:border-gray-200/70 lg:dark:border-gray-700 lg:shadow-sm lg:overflow-hidden">
          <div className="lg:p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 lg:gap-6">

              {/* Left column: Camera + sign strip + controls */}
              <div>
                {/* Camera — no outer padding on mobile, natural on desktop */}
                <div className="px-2 pt-2 lg:p-0">
                  <Camera ref={cameraRef} isTranslating={isTranslating} landmarks={lastLandmarks} />
                </div>

                {/* Mobile sign feedback strip — hidden on desktop */}
                <div className="lg:hidden px-2 pt-2 space-y-1.5">
                  <div className="rounded-lg border border-blue-100 dark:border-blue-900 bg-blue-50/80 dark:bg-blue-950/20 px-3 py-2.5 min-h-[48px]">
                    {detectedSigns.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 items-center">
                        {detectedSigns.slice(-24).map((sign, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-200 border border-blue-200/70 dark:border-blue-800/60"
                          >
                            {sign}
                          </span>
                        ))}
                        {detectedSigns.length > 24 && (
                          <span className="text-xs text-blue-400 dark:text-blue-500">+{detectedSigns.length - 24}</span>
                        )}
                      </div>
                    ) : lastSign ? (
                      <div className="flex items-center gap-2">
                        <span className={`text-2xl font-bold transition-opacity duration-300 ${isCapturing ? 'text-blue-400 opacity-60' : 'text-blue-600 dark:text-blue-400'}`}>
                          {lastSign}
                        </span>
                        {!isCapturing && lastConfidence > 0 && (
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            lastConfidence >= 0.85 ? 'bg-green-100 text-green-700 dark:bg-green-950/50 dark:text-green-300' :
                            lastConfidence >= 0.65 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950/50 dark:text-yellow-300' :
                            'bg-orange-100 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300'
                          }`}>
                            {Math.round(lastConfidence * 100)}%
                          </span>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400 dark:text-gray-500">
                        {isTranslating ? (lastGuidance || t.statusBar.defaultGuidance) : t.translator.steps[0]}
                      </p>
                    )}
                  </div>

                  {/* Current sentence pill on mobile */}
                  {currentSentence && (
                    <div className="rounded-lg bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 px-3 py-2">
                      <p className="text-base text-gray-800 dark:text-gray-100 leading-snug">{currentSentence}</p>
                    </div>
                  )}
                </div>

                {/* Desktop-only inline translate button */}
                {detectedSigns.length > 0 && (
                  <div className="hidden lg:block mt-4">
                    <button
                      type="button"
                      onClick={handleProcessTranslation}
                      className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors shadow-md"
                    >
                      {t.translator.translateButton}
                    </button>
                  </div>
                )}

                {/* Controls */}
                <div className="px-2 pt-2 lg:px-0 lg:pt-4">
                  <Controls onStart={handleStart} onStop={handleStop} onClear={handleClear} variant="embedded" />
                </div>

                {/* Status bar */}
                <div className="px-2 pt-2 lg:hidden">
                  <StatusBar detectionGuidance={lastGuidance} frameQuality={lastFrameQuality} variant="embedded" />
                </div>
              </div>

              {/* Right column: Translation panel */}
              <div className="px-2 pt-2 lg:px-0 lg:pt-0">
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
          </div>

          {/* Status bar — desktop only, inside card */}
          <div className="hidden lg:block">
            <div className="h-px bg-gray-200/70 dark:bg-gray-700" />
            <div className="p-6">
              <StatusBar detectionGuidance={lastGuidance} frameQuality={lastFrameQuality} variant="embedded" />
            </div>
          </div>
        </div>

        {/* How to Use — collapsible on mobile, expanded on desktop */}
        <details className="lg:hidden mx-2 mt-3 rounded-xl border border-blue-100 dark:border-blue-900 overflow-hidden">
          <summary className="px-4 py-3 bg-blue-50 dark:bg-blue-950/40 text-blue-900 dark:text-blue-100 font-semibold text-sm cursor-pointer select-none">
            {t.translator.howToUse}
          </summary>
          <div className="px-4 py-3 bg-blue-50/60 dark:bg-blue-950/20 border-t border-blue-100 dark:border-blue-900">
            <ol className="space-y-1.5 text-blue-800 dark:text-blue-200 text-sm">
              {t.translator.steps.map((step, index) => (
                <li key={step} className="flex items-start gap-2">
                  <span className="font-bold shrink-0">{index + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
            <p className="mt-3 text-xs text-blue-900/70 dark:text-blue-200/70">{t.translator.privacy}</p>
          </div>
        </details>

        <div className="hidden lg:block mt-8 bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            {t.translator.howToUse}
          </h3>
          <ol className="space-y-2 text-blue-800 dark:text-blue-200">
            {t.translator.steps.map((step, index) => (
              <li key={step} className="flex items-start gap-2">
                <span className="font-bold">{index + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-sm text-blue-900 dark:text-blue-200">{t.translator.privacy}</p>
        </div>

        {/* Bottom spacer on mobile so sticky bar doesn't hide last content */}
        <div className="lg:hidden h-20" />
      </main>

      {/* Sticky translate bar — mobile only, above the bottom nav */}
      {detectedSigns.length > 0 && (
        <div className="lg:hidden fixed bottom-16 inset-x-0 z-40 px-3 py-2 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200 dark:border-gray-700 shadow-[0_-4px_12px_rgba(0,0,0,0.08)]">
          <button
            type="button"
            onClick={handleProcessTranslation}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-xl font-semibold text-base shadow transition-colors"
          >
            {t.translator.translateButton} · {detectedSigns.length}
          </button>
        </div>
      )}

      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 mt-4 lg:mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 lg:py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-500 dark:text-gray-400">
            <p>{t.translator.footerProject}</p>
            <p className="text-xs">
              {t.translator.sessionId}: <span className="font-mono text-xs">{sessionId}</span>
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}
