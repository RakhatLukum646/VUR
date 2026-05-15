import { NavLink } from 'react-router-dom';
import { BookMarked, Languages } from 'lucide-react';
import { useUiText } from '../i18n';

function navLinkClassName(isActive: boolean): string {
  return [
    'flex flex-col items-center justify-center gap-1 flex-1 min-w-0 px-2 py-2.5 rounded-xl transition-colors',
    isActive
      ? 'bg-indigo-100 dark:bg-indigo-950/60 text-indigo-800 dark:text-indigo-200'
      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800',
  ].join(' ');
}

export function AppBottomNav() {
  const t = useUiText();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200/80 dark:border-gray-700 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md shadow-[0_-4px_20px_rgba(0,0,0,0.06)]"
      aria-label="Primary navigation"
    >
      <div className="max-w-7xl mx-auto flex items-stretch pb-[max(0.35rem,env(safe-area-inset-bottom))]">
        <NavLink
          to="/"
          end
          className={({ isActive }) => navLinkClassName(isActive)}
        >
          <Languages className="w-6 h-6 shrink-0" aria-hidden />
          <span className="text-xs font-medium text-center leading-tight">{t.nav.translator}</span>
        </NavLink>
        <NavLink
          to="/resources"
          className={({ isActive }) => navLinkClassName(isActive)}
        >
          <BookMarked className="w-6 h-6 shrink-0" aria-hidden />
          <span className="text-xs font-medium text-center leading-tight px-0.5">
            {t.nav.resources}
          </span>
        </NavLink>
      </div>
    </nav>
  );
}
