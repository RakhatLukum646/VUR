import { Play, Square, RotateCcw, Mic, Globe } from 'lucide-react';
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
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${connectionStatus === 'connecting' ? 'animate-pulse' : ''}`} />
          <div>
            <p className="text-sm font-medium text-gray-700">{getStatusText()}</p>
            <p className="text-xs text-gray-500">
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
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors shadow-md"
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
            className="flex items-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 text-gray-700 rounded-lg font-medium transition-colors"
          >
            <RotateCcw className="w-5 h-5" />
            Clear
          </button>
        </div>

        {/* Language + Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          {/* Language Selector */}
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-indigo-500" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as typeof language)}
              disabled={isTranslating}
              className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Mic className="w-4 h-4 text-blue-500" />
            <span>{detectedSigns.length} signs</span>
          </div>
          
          {isTranslating && (
            <div className="flex items-center gap-2 text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="font-medium">Translating...</span>
            </div>
          )}
        </div>
      </div>

      {/* Help Text */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          <span className="font-medium">Tip:</span> Position your hand clearly in front of the camera. 
          The system recognizes Russian Sign Language (RSL) gestures. Hold each sign for ~1 second, then pause between words.
        </p>
      </div>
    </div>
  );
};
