import { Play, Square, RotateCcw, Mic, Globe, ChevronDown } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LANGUAGE_OPTIONS } from '../types';

interface ControlsProps {
  onStart: () => void;
  onStop: () => void;
  onClear: () => void;
}

export const Controls = ({ onStart, onStop, onClear }: ControlsProps) => {
  const { isTranslating, connectionStatus, detectedSigns, language, setLanguage } = useAppStore();

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6 border border-gray-100 dark:border-gray-700">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${connectionStatus === 'connecting' ? 'animate-pulse' : ''}`} />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-200">{getStatusText()}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              WebSocket {connectionStatus === 'connected' ? 'active' : 'inactive'}
            </p>
          </div>
        </div>

        {/* Main Controls */}
        <div className="flex items-center gap-3">
          {!isTranslating ? (
            <button
              onClick={onStart}
              disabled={connectionStatus === 'connecting'}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 text-white rounded-lg font-medium transition-colors shadow-md"
            >
              <Play className="w-5 h-5" />
              Start Translation
            </button>
          ) : (
            <button
              onClick={onStop}
              className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors shadow-md"
            >
              <Square className="w-5 h-5" />
              Stop
            </button>
          )}

          <button
            onClick={onClear}
            disabled={detectedSigns.length === 0}
            className="flex items-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:text-gray-400 text-gray-700 dark:text-gray-200 rounded-lg font-medium transition-colors"
          >
            <RotateCcw className="w-5 h-5" />
            Clear
          </button>
        </div>

        {/* Language + Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
          {/* Language Selector */}
          <div className="group inline-flex h-10 items-center gap-2 rounded-lg px-3 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800/70 transition-[background-color,color] duration-200 ease-out">
            <Globe className="w-4 h-4 shrink-0 opacity-80 text-indigo-600 dark:text-indigo-400" aria-hidden />
            <select
              value={language}
              onChange={(e) => {
                const next = LANGUAGE_OPTIONS.find((opt) => opt.value === e.target.value);
                if (next) setLanguage(next.value);
              }}
              title="Translation language"
              aria-label="Translation language"
              className="h-8 max-w-[12rem] cursor-pointer appearance-none bg-transparent py-0 pl-0 pr-7 text-sm font-medium text-gray-900 dark:text-gray-100 outline-none border-0 focus:ring-0"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none -ml-6 w-4 h-4 shrink-0 opacity-50" aria-hidden />
          </div>

          <div className="flex items-center gap-2">
            <Mic className="w-4 h-4 text-blue-500" />
            <span>{detectedSigns.length} signs</span>
          </div>
          
          {isTranslating && (
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="font-medium">Translating...</span>
            </div>
          )}
        </div>
      </div>

      {/* Help Text */}
      <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          <span className="font-medium">Tip:</span> Position your hand clearly in front of the camera. 
          The system recognizes Russian Sign Language (RSL) gestures. Hold each sign for ~1 second, then pause between words.
        </p>
      </div>
    </div>
  );
};
