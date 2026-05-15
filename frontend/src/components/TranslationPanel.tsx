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
import { translateSigns } from '../services/api';
import { MenuSelect } from './MenuSelect';
import { useUiText } from '../i18n';

interface TranslationPanelProps {
  lastSign: string | null;
  confidence: number;
  guidance: string | null;
  frameQuality: number;
  stability: number;
  sequenceLength: number;
  handDetected: boolean;
}

function getConfidenceExplanation(
  confidence: number,
  handDetected: boolean,
  labels: {
    noHand: string;
    highConfidence: string;
    moderateConfidence: string;
    lowConfidence: string;
  }
) {
  if (!handDetected) {
    return labels.noHand;
  }

  if (confidence >= 0.85) {
    return labels.highConfidence;
  }

  if (confidence >= 0.65) {
    return labels.moderateConfidence;
  }

  return labels.lowConfidence;
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
  const t = useUiText();
  const { currentSentence, detectedSigns, language, sessionId, setCurrentSentence, addToHistory, translationHistory } =
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
  const [showAllVoices, setShowAllVoices] = useState(false);

  const visibleVoices = useMemo(() => {
    const lang = (language || 'ru').toLowerCase();
    const prefix =
      lang === 'kz'
        ? 'kk'
        : lang === 'en'
          ? 'en'
          : 'ru';

    const matchesPrefix = voices.filter((v) =>
      v.lang.toLowerCase().startsWith(`${prefix}-`) || v.lang.toLowerCase() === prefix
    );

    const candidates = matchesPrefix.length > 0 ? matchesPrefix : voices;
    const max = showAllVoices ? candidates.length : 8;
    return candidates.slice(0, max);
  }, [language, showAllVoices, voices]);

  const canExpandVoices = useMemo(() => {
    const lang = (language || 'ru').toLowerCase();
    const prefix =
      lang === 'kz'
        ? 'kk'
        : lang === 'en'
          ? 'en'
          : 'ru';

    const matchesPrefix = voices.filter((v) =>
      v.lang.toLowerCase().startsWith(`${prefix}-`) || v.lang.toLowerCase() === prefix
    );
    const candidates = matchesPrefix.length > 0 ? matchesPrefix : voices;
    return candidates.length > 8;
  }, [language, voices]);

  const signsDisplay = useMemo(() => {
    const last = translationHistory[translationHistory.length - 1];
    return last ? last.signs.slice(-20).join(' ') : '';
  }, [translationHistory]);
  const recentHistory = translationHistory.slice(-5).reverse();
  const confidenceExplanation = getConfidenceExplanation(
    confidence,
    handDetected,
    t.panel
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
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg overflow-hidden flex flex-col h-full border border-gray-100 dark:border-gray-700">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-700 dark:to-indigo-800 px-6 py-4">
        <h2 className="text-white font-semibold flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          {t.panel.title}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="rounded-xl border border-blue-100 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/40 p-4 space-y-4">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium uppercase tracking-wide">
              {t.panel.currentDetection}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-blue-600 dark:text-blue-400 min-w-[60px]">
              {lastSign || '-'}
            </div>
            <div className="flex-1 space-y-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm text-gray-600 dark:text-gray-400">{t.panel.classifierConfidence}</span>
                  <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${(confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {Math.round((confidence || 0) * 100)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{confidenceExplanation}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-white dark:bg-gray-800 px-3 py-2">
                  <div className="mb-1 flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                    <Gauge className="w-3.5 h-3.5" />
                    {t.panel.frameQuality}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 transition-all duration-300"
                        style={{ width: `${frameQuality * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      {Math.round(frameQuality * 100)}%
                    </span>
                  </div>
                </div>

                <div className="rounded-lg bg-white dark:bg-gray-800 px-3 py-2">
                  <div className="mb-1 flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                    <Eye className="w-3.5 h-3.5" />
                    {t.panel.stability}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-violet-500 transition-all duration-300"
                        style={{ width: `${stability * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      {Math.round(stability * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-blue-100 dark:border-blue-900 bg-white dark:bg-gray-800 px-4 py-3">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
              {guidance ?? t.statusBar.defaultGuidance}
            </p>
            <p className="mt-1 text-xs text-blue-700 dark:text-blue-300">
              {t.panel.bufferedSigns}: {sequenceLength}
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            {t.panel.detectedSigns}
          </h3>
          <div className="bg-gray-50 dark:bg-gray-800/80 rounded-lg p-4 min-h-[80px]">
            {signsDisplay ? (
              <p className="text-lg font-mono text-gray-800 dark:text-gray-100 break-all">
                {signsDisplay}
              </p>
            ) : (
              <p className="text-gray-400 dark:text-gray-500 italic">{t.panel.noSignsDetected}</p>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {detectedSigns.length} {t.panel.signsDetected}
          </p>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-200">
              {t.panel.translatedSentence}
            </h3>
            {isSupported && currentSentence && (
              <div className="flex items-center gap-2">
                {voices.length > 0 && (
                  <div className="inline-flex items-center gap-2">
                    <Volume2 className="w-4 h-4 shrink-0 opacity-80 text-blue-600 dark:text-blue-400" aria-hidden />
                    <MenuSelect
                      value={selectedVoiceURI ?? ''}
                      ariaLabel={t.panel.voice}
                      options={[
                        {
                          value: '',
                          label: t.panel.autoVoice,
                          textLabel: t.panel.autoVoice,
                        },
                        ...visibleVoices.map((v) => ({
                          value: v.voiceURI,
                          label: v.name,
                          textLabel: v.name,
                        })),
                      ]}
                      onChange={(nextValue) =>
                        setSelectedVoiceURI(nextValue ? nextValue : null)
                      }
                      className="relative"
                      buttonClassName="inline-flex h-9 items-center gap-2 rounded-lg px-3 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/70 transition-colors"
                      menuClassName="absolute left-0 z-50 mt-2 w-72 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg overflow-hidden"
                    />
                  </div>
                )}
                {voices.length > 0 && canExpandVoices && (
                  <button
                    type="button"
                    onClick={() => setShowAllVoices((v) => !v)}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-semibold border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/70 transition-colors"
                    title={showAllVoices ? t.panel.showFewerVoices : t.panel.showAllVoices}
                  >
                    {showAllVoices ? t.panel.showLess : t.panel.showAll}
                  </button>
                )}
                {activeVoice && (
                  <span className="hidden lg:inline text-xs text-gray-500 dark:text-gray-400">
                    {t.panel.reading}: {activeVoice.name} ({activeVoice.lang})
                  </span>
                )}
                {translationHistory.length > 0 && (
                  <button
                    onClick={handleRetranslate}
                    disabled={retranslating}
                    title={t.panel.retranslateTitle}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-emerald-200 dark:border-emerald-900 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200 hover:bg-emerald-100 dark:hover:bg-emerald-950/70 disabled:opacity-60 transition-colors"
                  >
                    {retranslating ? t.panel.retranslating : t.panel.retranslate}
                  </button>
                )}
                {isSpeaking && activeTextKey === 'current' && (
                  <button
                    onClick={() => (isPaused ? resume() : pause())}
                    title={isPaused ? t.panel.resume : t.panel.pause}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    {isPaused ? t.panel.resume : t.panel.pause}
                  </button>
                )}
                <button
                  onClick={handleSpeakCurrent}
                  title={
                    isSpeaking && activeTextKey === 'current'
                      ? t.panel.stopSpeaking
                      : t.panel.readAloud
                  }
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    isSpeaking && activeTextKey === 'current'
                      ? 'bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-950/60 dark:text-red-300 dark:hover:bg-red-950'
                      : 'bg-blue-100 text-blue-600 hover:bg-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:hover:bg-blue-900/60'
                  }`}
                >
                  {isSpeaking && activeTextKey === 'current' ? (
                    <>
                      <VolumeX className="w-3.5 h-3.5" />
                      {t.panel.stop}
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5" />
                      {t.panel.readAloud}
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
          <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 rounded-lg p-4 min-h-[80px]">
            {currentSentence ? (
              <p className="text-lg text-gray-800 dark:text-gray-100">
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
                          ? 'bg-yellow-200 dark:bg-yellow-700/50 rounded-sm'
                          : undefined
                      }
                    >
                      {t.text}
                    </span>
                  );
                })}
              </p>
            ) : (
              <p className="text-gray-400 dark:text-gray-500 italic">
                {t.panel.translationPlaceholder}
              </p>
            )}
          </div>
        </div>

        {recentHistory.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2 flex items-center gap-2">
              <History className="w-4 h-4" />
              {t.panel.recentHistory}
            </h3>
            <div className="space-y-2">
              {recentHistory.map((item, index) => (
                <div
                  key={index}
                  className="bg-gray-50 dark:bg-gray-800/80 rounded-lg p-3 text-sm flex items-start gap-2"
                >
                  <div className="flex-1">
                    <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">
                      {item.signs.join(' ')}
                    </div>
                    <div className="text-gray-800 dark:text-gray-100 font-medium">
                      {item.translation}
                    </div>
                  </div>
                  {isSupported && (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTextKey(index);
                        speak(item.translation, language);
                      }}
                      title={t.panel.readAloud}
                      aria-label={t.panel.readAloud}
                      className="mt-0.5 p-1 rounded text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/50 transition-colors flex-shrink-0"
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
