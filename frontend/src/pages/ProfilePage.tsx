import { UserCircle, Mail, Shield, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-xl font-bold text-gray-900">Profile</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <div className="flex items-center gap-4 mb-8">
            <div className="bg-blue-100 p-4 rounded-full">
              <UserCircle className="w-10 h-10 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {user?.name || 'Unknown User'}
              </h2>
              <p className="text-gray-500">User profile information</p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-gray-200 p-5 bg-gray-50">
              <div className="flex items-center gap-2 mb-2 text-gray-600">
                <Mail className="w-4 h-4" />
                <span className="text-sm font-medium">Email</span>
              </div>
              <p className="text-gray-900 font-semibold">
                {user?.email || 'No email'}
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 p-5 bg-gray-50">
              <div className="flex items-center gap-2 mb-2 text-gray-600">
                <Shield className="w-4 h-4" />
                <span className="text-sm font-medium">Role</span>
              </div>
              <p className="text-gray-900 font-semibold">
                {user?.role || 'User'}
              </p>
            </div>
          </div>

          <div className="mt-8 flex gap-3">
            <button
              onClick={() => navigate('/')}
              className="px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors"
            >
              Back to Translator
            </button>

            <button
              onClick={handleLogout}
              className="px-5 py-3 rounded-lg bg-red-500 hover:bg-red-600 text-white font-medium transition-colors flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}