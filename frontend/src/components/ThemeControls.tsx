import { ChevronDown, Check, Glasses, Monitor, Moon, Sun } from 'lucide-react';
import { useMemo, useRef, useState } from 'react';
import type { ColorblindMode, ColorScheme } from '../store/useThemeStore';
import { useThemeStore } from '../store/useThemeStore';
import { useThemeControlsMenuClose } from '../hooks/useThemeControlsMenuClose';

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
  const [isColorMenuOpen, setIsColorMenuOpen] = useState(false);
  const colorMenuRef = useRef<HTMLDivElement>(null);

  const activeColorblindLabel = useMemo(() => {
    return COLORBLIND_OPTIONS.find((opt) => opt.value === colorblindMode)?.label ?? 'Default';
  }, [colorblindMode]);

  useThemeControlsMenuClose(
    isColorMenuOpen,
    () => setIsColorMenuOpen(false),
    colorMenuRef
  );

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

      <div className="relative" ref={colorMenuRef}>
        <button
          type="button"
          onClick={() => setIsColorMenuOpen((v) => !v)}
          title="Color vision assist (approximate full-page tint)"
          aria-label="Color vision assist"
          aria-haspopup="menu"
          aria-expanded={isColorMenuOpen}
          className="group inline-flex h-9 items-center gap-2 rounded-lg px-3 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800/70 hover:text-gray-900 dark:hover:text-gray-100 transition-[background-color,color] duration-200 ease-out"
        >
          <Glasses className="w-4 h-4 shrink-0 opacity-80" aria-hidden />
          <span className="text-xs font-medium text-gray-800 dark:text-gray-100">
            {activeColorblindLabel}
          </span>
          <ChevronDown
            className={`w-3.5 h-3.5 shrink-0 opacity-50 transition-transform ${
              isColorMenuOpen ? 'rotate-180' : ''
            }`}
            aria-hidden
          />
        </button>

        {isColorMenuOpen && (
          <div
            role="menu"
            aria-label="Color vision assist"
            className="absolute right-0 z-50 mt-2 w-56 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg overflow-hidden"
          >
            <div className="p-2">
              {COLORBLIND_OPTIONS.map((opt) => {
                const isActive = opt.value === colorblindMode;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    role="menuitemradio"
                    aria-checked={isActive}
                    onClick={() => {
                      setColorblindMode(opt.value);
                      setIsColorMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-100'
                        : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/70'
                    }`}
                  >
                    <span className="font-medium">{opt.label}</span>
                    {isActive && <Check className="w-4 h-4 text-indigo-600 dark:text-indigo-300" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
