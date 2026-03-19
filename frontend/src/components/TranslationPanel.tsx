import React from 'react';
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

export const TranslationPanel: React.FC<TranslationPanelProps> = ({
  lastSign,
  confidence,
  guidance,
  frameQuality,
  stability,
  sequenceLength,
  handDetected,
}) => {
  const { currentSentence, detectedSigns, language, translationHistory } =
    useAppStore();
  const { isSpeaking, isSupported, speak, stop } = useSpeech();

  const signsDisplay = detectedSigns.slice(-20).join(' ');
  const recentHistory = translationHistory.slice(-5).reverse();
  const confidenceExplanation = getConfidenceExplanation(
    confidence,
    handDetected
  );

  const handleSpeak = (text: string) => {
    if (isSpeaking) {
      stop();
    } else {
      speak(text, language);
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
              <button
                onClick={() => handleSpeak(currentSentence)}
                title={isSpeaking ? 'Stop speaking' : 'Read aloud'}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  isSpeaking
                    ? 'bg-red-100 text-red-600 hover:bg-red-200'
                    : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                }`}
              >
                {isSpeaking ? (
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
            )}
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 min-h-[80px]">
            {currentSentence ? (
              <p className="text-lg text-gray-800">{currentSentence}</p>
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
                      onClick={() => speak(item.translation, language)}
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
