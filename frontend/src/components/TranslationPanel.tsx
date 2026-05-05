import React, { useMemo, useState } from 'react';
import {
  Activity,
  Eye,
  Gauge,
  History,
  MessageSquare,
  Sparkles,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { useSpeech } from '../hooks/useSpeech';
import { useAppStore } from '../store/useAppStore';
import { LANGUAGE_OPTIONS } from '../types';
import { translateSigns } from '../services/api';

interface TranslationPanelProps {
  lastSign: string | null;
  confidence: number;
  guidance: string | null;
  frameQuality: number;
  stability: number;
  sequenceLength: number;
  handDetected: boolean;
}

function getConfidenceExplanation(confidence: number, handDetected: boolean) {
  if (!handDetected) {
    return 'No hand detected yet.';
  }

  if (confidence >= 0.85) {
    return 'High confidence. The hand shape looks consistent.';
  }

  if (confidence >= 0.65) {
    return 'Moderate confidence. Hold the gesture a bit longer.';
  }

  return 'Low confidence. Adjust framing, lighting, or hand shape.';
}

type TextToken = {
  text: string;
  start: number;
  end: number;
};

function tokenizeWithOffsets(text: string): TextToken[] {
  const tokens: TextToken[] = [];
  const re = /\S+\s*/g;
  let match: RegExpExecArray | null;

  while ((match = re.exec(text)) !== null) {
    const raw = match[0];
    const start = match.index;
    const end = start + raw.length;
    tokens.push({ text: raw, start, end });
  }

  return tokens;
}

export const TranslationPanel: React.FC<TranslationPanelProps> = ({
  lastSign,
  confidence,
  guidance,
  frameQuality,
  stability,
  sequenceLength,
  handDetected,
}) => {
  const { currentSentence, detectedSigns, language, sessionId, setLanguage, setCurrentSentence, addToHistory, translationHistory } =
    useAppStore();
  const {
    isSpeaking,
    isPaused,
    isSupported,
    speak,
    stop,
    pause,
    resume,
    activeBoundary,
    speakingText,
    voices,
    selectedVoiceURI,
    setSelectedVoiceURI,
    activeVoice,
  } = useSpeech();
  const [activeTextKey, setActiveTextKey] = useState<'current' | number | null>(null);
  const [retranslating, setRetranslating] = useState(false);

  const signsDisplay = useMemo(() => {
    const last = translationHistory[translationHistory.length - 1];
    return last ? last.signs.slice(-20).join(' ') : '';
  }, [translationHistory]);
  const recentHistory = translationHistory.slice(-5).reverse();
  const confidenceExplanation = getConfidenceExplanation(
    confidence,
    handDetected
  );

  const highlightRange = useMemo(() => {
    if (!isSpeaking) return null;
    if (!activeBoundary) return null;
    if (!speakingText) return null;

    const start = activeBoundary.charIndex;
    const length =
      activeBoundary.charLength > 0 ? activeBoundary.charLength : 1;
    return { start, end: start + length };
  }, [activeBoundary, isSpeaking, speakingText]);

  const currentSentenceTokens = useMemo(
    () => tokenizeWithOffsets(currentSentence),
    [currentSentence]
  );

  const handleSpeakCurrent = () => {
    if (!currentSentence) return;
    if (isSpeaking && activeTextKey === 'current') {
      stop();
      setActiveTextKey(null);
      return;
    }
    setActiveTextKey('current');
    speak(currentSentence, language);
  };

  const handleRetranslate = async () => {
    const last = translationHistory[translationHistory.length - 1];
    if (!last) return;
    setRetranslating(true);
    try {
      const result = await translateSigns(last.signs, sessionId, undefined, language);
      setCurrentSentence(result.translation);
      addToHistory({
        signs: last.signs,
        translation: result.translation,
        timestamp: Date.now(),
      });
    } finally {
      setRetranslating(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden flex flex-col h-full">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
        <h2 className="text-white font-semibold flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Translation Panel
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-4 space-y-4">
          <div className="flex items-center gap-2 text-blue-700">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium uppercase tracking-wide">
              Current Detection
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-blue-600 min-w-[60px]">
              {lastSign || '-'}
            </div>
            <div className="flex-1 space-y-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm text-gray-600">Classifier confidence</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${(confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    {Math.round((confidence || 0) * 100)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500">{confidenceExplanation}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-white px-3 py-2">
                  <div className="mb-1 flex items-center gap-2 text-xs font-medium text-gray-500">
                    <Gauge className="w-3.5 h-3.5" />
                    Frame quality
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 transition-all duration-300"
                        style={{ width: `${frameQuality * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-700">
                      {Math.round(frameQuality * 100)}%
                    </span>
                  </div>
                </div>

                <div className="rounded-lg bg-white px-3 py-2">
                  <div className="mb-1 flex items-center gap-2 text-xs font-medium text-gray-500">
                    <Eye className="w-3.5 h-3.5" />
                    Stability
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-violet-500 transition-all duration-300"
                        style={{ width: `${stability * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-700">
                      {Math.round(stability * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-blue-100 bg-white px-4 py-3">
            <p className="text-sm font-medium text-blue-900">
              {guidance ?? 'Show one hand in the frame to start detection.'}
            </p>
            <p className="mt-1 text-xs text-blue-700">
              Buffered signs in current phrase: {sequenceLength}
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            Detected Signs
          </h3>
          <div className="bg-gray-50 rounded-lg p-4 min-h-[80px]">
            {signsDisplay ? (
              <p className="text-lg font-mono text-gray-800 break-all">
                {signsDisplay}
              </p>
            ) : (
              <p className="text-gray-400 italic">No signs detected yet...</p>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {detectedSigns.length} sign{detectedSigns.length !== 1 ? 's' : ''} detected
          </p>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-700">
              Translated Sentence
            </h3>
            {isSupported && currentSentence && (
              <div className="flex items-center gap-2">
                <select
                  value={language}
                  onChange={(e) => {
                    const next = LANGUAGE_OPTIONS.find((opt) => opt.value === e.target.value);
                    if (next) setLanguage(next.value);
                  }}
                  title="Language"
                  className="px-2 py-1 rounded-full text-xs bg-white border border-gray-200 text-gray-700"
                >
                  {LANGUAGE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.flag} {opt.label}
                    </option>
                  ))}
                </select>
                {voices.length > 0 && (
                  <select
                    value={selectedVoiceURI ?? ''}
                    onChange={(e) =>
                      setSelectedVoiceURI(e.target.value ? e.target.value : null)
                    }
                    title="Voice"
                    className="max-w-[220px] px-2 py-1 rounded-full text-xs bg-white border border-gray-200 text-gray-700"
                  >
                    <option value="">Auto voice</option>
                    {voices.map((v) => (
                      <option key={v.voiceURI} value={v.voiceURI}>
                        {v.name} ({v.lang})
                      </option>
                    ))}
                  </select>
                )}
                {activeVoice && (
                  <span className="hidden lg:inline text-xs text-gray-500">
                    Reading: {activeVoice.name} ({activeVoice.lang})
                  </span>
                )}
                {translationHistory.length > 0 && (
                  <button
                    onClick={handleRetranslate}
                    disabled={retranslating}
                    title="Re-translate last phrase with current language"
                    className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 hover:bg-emerald-200 disabled:opacity-60 transition-colors"
                  >
                    {retranslating ? 'Translating…' : 'Re-translate'}
                  </button>
                )}
                {isSpeaking && activeTextKey === 'current' && (
                  <button
                    onClick={() => (isPaused ? resume() : pause())}
                    title={isPaused ? 'Resume' : 'Pause'}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                  >
                    {isPaused ? 'Resume' : 'Pause'}
                  </button>
                )}
                <button
                  onClick={handleSpeakCurrent}
                  title={
                    isSpeaking && activeTextKey === 'current'
                      ? 'Stop speaking'
                      : 'Read aloud'
                  }
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    isSpeaking && activeTextKey === 'current'
                      ? 'bg-red-100 text-red-600 hover:bg-red-200'
                      : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                  }`}
                >
                  {isSpeaking && activeTextKey === 'current' ? (
                    <>
                      <VolumeX className="w-3.5 h-3.5" />
                      Stop
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5" />
                      Read aloud
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 min-h-[80px]">
            {currentSentence ? (
              <p className="text-lg text-gray-800">
                {currentSentenceTokens.map((t, idx) => {
                  const shouldHighlight =
                    activeTextKey === 'current' &&
                    highlightRange !== null &&
                    t.start < highlightRange.end &&
                    t.end > highlightRange.start;

                  return (
                    <span
                      key={`${idx}-${t.start}`}
                      className={
                        shouldHighlight
                          ? 'bg-yellow-200 rounded-sm'
                          : undefined
                      }
                    >
                      {t.text}
                    </span>
                  );
                })}
              </p>
            ) : (
              <p className="text-gray-400 italic">
                Translation will appear here when you complete a sign sequence...
              </p>
            )}
          </div>
        </div>

        {recentHistory.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <History className="w-4 h-4" />
              Recent History
            </h3>
            <div className="space-y-2">
              {recentHistory.map((item, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-3 text-sm flex items-start gap-2"
                >
                  <div className="flex-1">
                    <div className="text-gray-500 text-xs mb-1">
                      {item.signs.join(' ')}
                    </div>
                    <div className="text-gray-800 font-medium">
                      {item.translation}
                    </div>
                  </div>
                  {isSupported && (
                    <button
                      onClick={() => {
                        setActiveTextKey(index);
                        speak(item.translation, language);
                      }}
                      title="Read aloud"
                      className="mt-0.5 p-1 rounded text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors flex-shrink-0"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
