import { Play, Square, RotateCcw, Mic } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

interface ControlsProps {
  onStart: () => void;
  onStop: () => void;
  onClear: () => void;
}

export const Controls = ({ onStart, onStop, onClear }: ControlsProps) => {
  const { isTranslating, connectionStatus, detectedSigns } = useAppStore();

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

        {/* Stats */}
        <div className="flex items-center gap-6 text-sm text-gray-600">
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
          The system recognizes ASL signs (A-Z, 0-9). Pause between words for better recognition.
        </p>
      </div>
    </div>
  );
};
