import { Play, Square, RotateCcw, Mic, Globe } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LANGUAGE_OPTIONS } from '../types';
import { MenuSelect } from './MenuSelect';
import { useUiText } from '../i18n';

interface ControlsProps {
  onStart: () => void;
  onStop: () => void;
  onClear: () => void;
  variant?: 'card' | 'embedded';
}

export const Controls = ({
  onStart,
  onStop,
  onClear,
  variant = 'card',
}: ControlsProps) => {
  const { isTranslating, connectionStatus, detectedSigns, language, setLanguage } = useAppStore();
  const t = useUiText();
  const languageOptions = LANGUAGE_OPTIONS.map((opt) => ({
    value: opt.value,
    label: (
      <span className="inline-flex items-center gap-2">
        <span aria-hidden>{opt.flag}</span>
        <span>{opt.label}</span>
      </span>
    ),
    textLabel: `${opt.label}`,
  }));

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
        return t.status.connected;
      case 'connecting':
        return t.status.connecting;
      case 'error':
        return t.status.error;
      default:
        return t.status.disconnected;
    }
  };

  const containerClassName =
    variant === 'embedded'
      ? 'rounded-xl border border-gray-200/70 dark:border-gray-700 bg-gray-50/70 dark:bg-gray-950/20 p-4'
      : 'bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6 border border-gray-100 dark:border-gray-700';
  const helpTextClassName =
    variant === 'embedded'
      ? 'mt-4 pt-4 border-t border-gray-200/70 dark:border-gray-700'
      : 'mt-4 pt-4 border-t border-gray-100 dark:border-gray-700';

  return (
    <div className={containerClassName}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${connectionStatus === 'connecting' ? 'animate-pulse' : ''}`} />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-200">{getStatusText()}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {connectionStatus === 'connected' ? t.status.websocketActive : t.status.websocketInactive}
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
              {t.controls.start}
            </button>
          ) : (
            <button
              onClick={onStop}
              className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors shadow-md"
            >
              <Square className="w-5 h-5" />
              {t.controls.stop}
            </button>
          )}

          <button
            onClick={onClear}
            disabled={detectedSigns.length === 0}
            className="flex items-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:text-gray-400 text-gray-700 dark:text-gray-200 rounded-lg font-medium transition-colors"
          >
            <RotateCcw className="w-5 h-5" />
            {t.controls.clear}
          </button>
        </div>

        {/* Language + Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
          {/* Language Selector */}
          <div className="inline-flex items-center gap-2">
            <Globe className="w-4 h-4 shrink-0 opacity-80 text-indigo-600 dark:text-indigo-400" aria-hidden />
            <MenuSelect
              value={language}
              options={languageOptions}
              ariaLabel={t.translationLanguage}
              onChange={(nextValue) => {
                const next = LANGUAGE_OPTIONS.find((opt) => opt.value === nextValue);
                if (next) setLanguage(next.value);
              }}
              buttonClassName="inline-flex h-10 items-center gap-2 rounded-lg px-3 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/70 transition-colors"
              menuClassName="absolute left-0 z-50 mt-2 w-64 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg overflow-hidden"
              className="relative"
            />
          </div>

          <div className="flex items-center gap-2">
            <Mic className="w-4 h-4 text-blue-500" />
            <span>{detectedSigns.length} {t.controls.signs}</span>
          </div>
          
          {isTranslating && (
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="font-medium">{t.controls.translating}</span>
            </div>
          )}
        </div>
      </div>

      {/* Help Text */}
      <div className={helpTextClassName}>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          <span className="font-medium">{t.controls.tipLabel}</span> {t.controls.tip}
        </p>
      </div>
    </div>
  );
};
