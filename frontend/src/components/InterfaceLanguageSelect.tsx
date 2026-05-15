import { Languages } from 'lucide-react';
import { UI_LANGUAGES, useUiText } from '../i18n';
import { useAppStore } from '../store/useAppStore';
import { MenuSelect } from './MenuSelect';

export function InterfaceLanguageSelect() {
  const t = useUiText();
  const interfaceLanguage = useAppStore((state) => state.interfaceLanguage);
  const setInterfaceLanguage = useAppStore((state) => state.setInterfaceLanguage);

  const options = UI_LANGUAGES.map((lang) => ({
    value: lang.value,
    label: (
      <span className="inline-flex items-center gap-2">
        <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[11px] font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200">
          {lang.shortLabel}
        </span>
        <span>{lang.label}</span>
      </span>
    ),
    textLabel: lang.label,
  }));

  return (
    <div className="inline-flex items-center gap-2">
      <Languages className="h-4 w-4 shrink-0 text-indigo-600 dark:text-indigo-400" aria-hidden />
      <MenuSelect
        value={interfaceLanguage}
        options={options}
        ariaLabel={t.interfaceLanguage}
        onChange={(next) => {
          if (next === 'en' || next === 'ru' || next === 'kz') {
            setInterfaceLanguage(next);
          }
        }}
        buttonClassName="inline-flex h-10 items-center gap-2 rounded-lg px-3 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/70 transition-colors"
        menuClassName="absolute right-0 z-50 mt-2 w-56 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg overflow-hidden"
      />
    </div>
  );
}
