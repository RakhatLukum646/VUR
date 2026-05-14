import { Outlet, useNavigate } from 'react-router-dom';
import { AppHeader } from '../components/AppHeader';
import { AppBottomNav } from '../components/AppBottomNav';
import { useAuthStore } from '../store/useAuthStore';
import { logoutUser } from '../services/authApi';

export default function MainLayout() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // Clear local auth state even if the backend session is already gone.
    }
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 bg-gradient-to-b from-indigo-50 via-transparent to-transparent dark:from-indigo-950/30"
      />
      <AppHeader
        userName={user?.name}
        userRole={user?.role ?? null}
        onLogout={handleLogout}
      />
      <div className="flex-1 pb-24">
        <Outlet />
      </div>
      <AppBottomNav />
    </div>
  );
}
