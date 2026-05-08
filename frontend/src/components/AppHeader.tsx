import { ArrowLeft, Github, LogOut, Shield, UserCircle } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ThemeControls } from './ThemeControls';

type AppHeaderProps = {
  userName?: string | null;
  userRole?: 'user' | 'admin' | null;
  onLogout?: () => void;
  variant?: 'app' | 'auth';
};

export function AppHeader({
  userName,
  userRole,
  onLogout,
  variant = 'app',
}: AppHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const isOnProfile = location.pathname === '/profile';
  const isAuthShell = variant === 'auth';
  const logoSizeClassName = isAuthShell ? 'h-10 w-10 sm:h-11 sm:w-11' : 'h-11 w-11 sm:h-12 sm:w-12';

  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3 sm:gap-4 min-w-0">
            <img
              src="/logo.png"
              alt="SignZhan"
              width={96}
              height={96}
              className={`${logoSizeClassName} object-contain`}
              decoding="async"
            />
            <div className="min-w-0">
              <div className="flex items-baseline gap-1 min-w-0">
                <span className="text-xl sm:text-2xl font-bold tracking-tight text-indigo-700 dark:text-indigo-400">
                  Sign
                </span>
                <span className="text-xl sm:text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                  Zhan
                </span>
              </div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 leading-snug">
                Real-Time Sign Language Translation
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 sm:gap-4 sm:justify-end">
            <ThemeControls />

            {!isAuthShell && isOnProfile && (
              <Link
                to="/"
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-700 dark:text-gray-200"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline text-sm">Back to translator</span>
              </Link>
            )}
            <a
              href="https://github.com/RakhatLukum646/VUR"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <Github className="w-5 h-5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>

            {!isAuthShell && userRole === 'admin' && (
              <Link
                to="/admin"
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-indigo-200 dark:border-indigo-900 bg-indigo-50/60 dark:bg-indigo-950/30 hover:bg-indigo-100/70 dark:hover:bg-indigo-950/50 transition-colors text-indigo-800 dark:text-indigo-200"
              >
                <Shield className="w-4 h-4" />
                <span className="hidden md:inline text-sm">Admin</span>
              </Link>
            )}

            {!isAuthShell && !isOnProfile && (
              <button
                type="button"
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <UserCircle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <span className="hidden md:inline text-sm text-gray-700 dark:text-gray-200">
                  {userName || 'Profile'}
                </span>
              </button>
            )}

            {!isAuthShell && onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-red-50 dark:hover:bg-red-950/40 hover:border-red-200 dark:hover:border-red-800 transition-colors text-gray-700 dark:text-gray-200 hover:text-red-600 dark:hover:text-red-400"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden md:inline text-sm">Logout</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
