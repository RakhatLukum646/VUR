import { BookOpen, Github, Hand, LogOut, UserCircle } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

type AppHeaderProps = {
  userName?: string | null;
  onLogout: () => void;
};

export function AppHeader({ userName, onLogout }: AppHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const isOnProfile = location.pathname === '/profile';

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Hand className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                AI Sign Language Translator
              </h1>
              <p className="text-sm text-gray-500">
                Real-time RSL (Russian Sign Language) translation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="https://github.com/RakhatLukum646/VUR"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <Github className="w-5 h-5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>

            <Link
              to="/docs"
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <BookOpen className="w-5 h-5" />
              <span className="hidden sm:inline">Docs</span>
            </Link>

            {!isOnProfile && (
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <UserCircle className="w-5 h-5 text-blue-600" />
                <span className="hidden md:inline text-sm text-gray-700">
                  {userName || 'Profile'}
                </span>
              </button>
            )}

            <button
              onClick={onLogout}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 hover:bg-red-50 hover:border-red-200 transition-colors text-gray-700 hover:text-red-600"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden md:inline text-sm">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

