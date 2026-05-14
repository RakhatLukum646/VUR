import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useThemeStore } from '../store/useThemeStore';

type ThemeSyncProps = {
  children: ReactNode;
};

function useSystemDark(): boolean {
  const [systemDark, setSystemDark] = useState(() => {
    if (typeof window === 'undefined') {
      return false;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => setSystemDark(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  return systemDark;
}

const THEME_TRANSITION_MS = 420;

export function ThemeSync({ children }: ThemeSyncProps) {
  const colorScheme = useThemeStore((s) => s.colorScheme);
  const colorblindMode = useThemeStore((s) => s.colorblindMode);
  const systemDark = useSystemDark();
  const isFirstThemeApply = useRef(true);

  const resolvedDark =
    colorScheme === 'dark' ||
    (colorScheme === 'system' && systemDark);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', resolvedDark);
    root.classList.remove('cb-protanopia', 'cb-deuteranopia', 'cb-tritanopia');
    if (colorblindMode !== 'none') {
      root.classList.add(`cb-${colorblindMode}`);
    }

    if (isFirstThemeApply.current) {
      isFirstThemeApply.current = false;
      return;
    }

    root.classList.add('theme-transition-active');
    const id = window.setTimeout(() => {
      root.classList.remove('theme-transition-active');
    }, THEME_TRANSITION_MS);
    return () => window.clearTimeout(id);
  }, [resolvedDark, colorblindMode]);

  return <>{children}</>;
}
