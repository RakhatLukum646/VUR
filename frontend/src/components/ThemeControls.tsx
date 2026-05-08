import { ChevronDown, Glasses, Monitor, Moon, Sun } from 'lucide-react';
import type { ColorblindMode, ColorScheme } from '../store/useThemeStore';
import { useThemeStore } from '../store/useThemeStore';

const COLORBLIND_OPTIONS: { value: ColorblindMode; label: string }[] = [
  { value: 'none', label: 'Default' },
  { value: 'protanopia', label: 'Protanopia' },
  { value: 'deuteranopia', label: 'Deuteranopia' },
  { value: 'tritanopia', label: 'Tritanopia' },
];

export function ThemeControls() {
  const colorScheme = useThemeStore((s) => s.colorScheme);
  const colorblindMode = useThemeStore((s) => s.colorblindMode);
  const setColorScheme = useThemeStore((s) => s.setColorScheme);
  const setColorblindMode = useThemeStore((s) => s.setColorblindMode);

  const cycleScheme = () => {
    const order: ColorScheme[] = ['light', 'dark', 'system'];
    const idx = order.indexOf(colorScheme);
    const next = order[(idx + 1) % order.length];
    setColorScheme(next);
  };

  const schemeTitle =
    colorScheme === 'light'
      ? 'Theme: light — next: dark'
      : colorScheme === 'dark'
        ? 'Theme: dark — next: system'
        : 'Theme: system — next: light';

  return (
    <div className="flex flex-wrap items-center gap-1 sm:gap-2">
      <button
        type="button"
        onClick={cycleScheme}
        title={schemeTitle}
        aria-label={schemeTitle}
        className="inline-flex h-9 w-9 items-center justify-center rounded-full text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/80 hover:text-gray-900 dark:hover:text-gray-100 active:scale-95 transition-[transform,background-color,color] duration-200 ease-out"
      >
        {colorScheme === 'light' && <Sun className="w-[18px] h-[18px] stroke-[1.5]" />}
        {colorScheme === 'dark' && <Moon className="w-[18px] h-[18px] stroke-[1.5]" />}
        {colorScheme === 'system' && <Monitor className="w-[18px] h-[18px] stroke-[1.5]" />}
      </button>

      <div className="group inline-flex h-9 items-center gap-2 rounded-lg px-3 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800/70 hover:text-gray-900 dark:hover:text-gray-100 transition-[background-color,color] duration-200 ease-out">
        <Glasses className="w-4 h-4 shrink-0 opacity-80" aria-hidden />
        <select
          value={colorblindMode}
          onChange={(e) =>
            setColorblindMode(e.target.value as ColorblindMode)
          }
          title="Color vision assist (approximate full-page tint)"
          aria-label="Color vision assist"
          className="h-7 max-w-[10rem] cursor-pointer appearance-none bg-transparent py-0 pl-0 pr-6 text-xs font-medium text-gray-800 dark:text-gray-100 outline-none border-0 focus:ring-0"
        >
          {COLORBLIND_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none -ml-5 w-3.5 h-3.5 shrink-0 opacity-50" aria-hidden />
      </div>
    </div>
  );
}
