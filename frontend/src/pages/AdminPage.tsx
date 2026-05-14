import { useEffect, useMemo, useState } from 'react';
import { Shield, Trash2, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { deleteUser, getAdminStats, listAdminUsers, setUserRole } from '../services/authApi';
import type { User } from '../types/auth';
import { AppHeader } from '../components/AppHeader';
import { logoutUser } from '../services/authApi';
import { useAuthStore } from '../store/useAuthStore';

type AdminStats = {
  total_users: number;
  verified_users: number;
  two_factor_enabled_users: number;
  admin_users: number;
};

export default function AdminPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

  const sortedUsers = useMemo(() => {
    const copy = [...users];
    copy.sort((a, b) => {
      const ra = a.role === 'admin' ? 0 : 1;
      const rb = b.role === 'admin' ? 0 : 1;
      if (ra !== rb) return ra - rb;
      return a.email.localeCompare(b.email);
    });
    return copy;
  }, [users]);

  useEffect(() => {
    setLoading(true);
    setMessage('');
    Promise.all([getAdminStats(), listAdminUsers(100, 0)])
      .then(([s, u]) => {
        setStats(s);
        setUsers(u.users);
      })
      .catch((e: unknown) => {
        setMessage(e instanceof Error ? e.message : 'Failed to load admin data');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleRoleChange = async (userId: string, nextRole: 'user' | 'admin') => {
    setMessage('');
    setBusyUserId(userId);
    try {
      const updated = await setUserRole(userId, nextRole);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : 'Failed to update role');
    } finally {
      setBusyUserId(null);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // Clear local auth state even if the backend session is already gone.
    }
    logout();
    navigate('/login');
  };

  const handleDeleteUser = async (u: User) => {
    setMessage('');
    const ok = window.confirm(`Delete user ${u.email}? This cannot be undone.`);
    if (!ok) return;

    setBusyUserId(u.id);
    try {
      await deleteUser(u.id);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
      setStats((prev) =>
        prev
          ? {
              ...prev,
              total_users: Math.max(0, prev.total_users - 1),
              verified_users: u.is_verified ? Math.max(0, prev.verified_users - 1) : prev.verified_users,
              two_factor_enabled_users: u.two_factor_enabled
                ? Math.max(0, prev.two_factor_enabled_users - 1)
                : prev.two_factor_enabled_users,
              admin_users: u.role === 'admin' ? Math.max(0, prev.admin_users - 1) : prev.admin_users,
            }
          : prev
      );
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : 'Failed to delete user');
    } finally {
      setBusyUserId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 bg-gradient-to-b from-indigo-50 via-transparent to-transparent dark:from-indigo-950/30"
      />

      <AppHeader
        userName={user?.name}
        userRole={user?.role ?? null}
        onLogout={handleLogout}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Shield className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              Admin Panel
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
              Users overview, verification status, and roles.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
            <Users className="w-4 h-4" />
            <span>{stats ? `${stats.total_users} users` : '—'}</span>
          </div>
        </div>

        {message && (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white/70 dark:bg-gray-900/60 backdrop-blur px-4 py-3 text-sm text-gray-700 dark:text-gray-200">
            {message}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total users"
            value={stats?.total_users}
            tone="indigo"
            loading={loading}
          />
          <StatCard
            label="Verified users"
            value={stats?.verified_users}
            tone="emerald"
            loading={loading}
          />
          <StatCard
            label="2FA enabled"
            value={stats?.two_factor_enabled_users}
            tone="amber"
            loading={loading}
          />
          <StatCard
            label="Admins"
            value={stats?.admin_users}
            tone="slate"
            loading={loading}
          />
        </div>

        <div className="rounded-2xl border border-gray-200/70 dark:border-gray-700 bg-white/80 dark:bg-gray-900/70 backdrop-blur shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-200/70 dark:border-gray-700 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">Users</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Showing {sortedUsers.length}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50/70 dark:bg-gray-950/20 text-gray-600 dark:text-gray-300">
                <tr>
                  <th className="text-left font-semibold px-5 py-3">Email</th>
                  <th className="text-left font-semibold px-5 py-3">Name</th>
                  <th className="text-left font-semibold px-5 py-3">Verified</th>
                  <th className="text-left font-semibold px-5 py-3">2FA</th>
                  <th className="text-left font-semibold px-5 py-3">Role</th>
                <th className="text-right font-semibold px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200/70 dark:divide-gray-700">
                {sortedUsers.map((u) => (
                  <tr key={u.id} className="text-gray-800 dark:text-gray-100">
                    <td className="px-5 py-3 font-mono text-xs">{u.email}</td>
                    <td className="px-5 py-3">{u.name}</td>
                    <td className="px-5 py-3">
                      {u.is_verified ? (
                        <span className="inline-flex rounded-full px-2 py-1 text-xs font-semibold bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200 border border-emerald-200/70 dark:border-emerald-900">
                          Yes
                        </span>
                      ) : (
                        <span className="inline-flex rounded-full px-2 py-1 text-xs font-semibold bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200 border border-amber-200/70 dark:border-amber-900">
                          No
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      {u.two_factor_enabled ? 'Enabled' : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <select
                        value={u.role ?? 'user'}
                        onChange={(e) => {
                          const next = e.target.value === 'admin' ? 'admin' : 'user';
                          void handleRoleChange(u.id, next);
                        }}
                        disabled={busyUserId === u.id}
                        className="h-9 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 text-sm font-semibold text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60"
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => void handleDeleteUser(u)}
                      disabled={busyUserId === u.id || u.id === user?.id}
                      title={u.id === user?.id ? 'You cannot delete your own account' : 'Delete user'}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-red-200 dark:border-red-900 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-200 hover:bg-red-100 dark:hover:bg-red-950/70 transition-colors disabled:opacity-60"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span className="hidden sm:inline text-sm font-semibold">Delete</span>
                    </button>
                  </td>
                  </tr>
                ))}
                {sortedUsers.length === 0 && (
                  <tr>
                    <td
                    colSpan={6}
                      className="px-5 py-10 text-center text-gray-500 dark:text-gray-400"
                    >
                      {loading ? 'Loading...' : 'No users found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
  loading,
}: {
  label: string;
  value: number | undefined;
  tone: 'indigo' | 'emerald' | 'amber' | 'slate';
  loading: boolean;
}) {
  const toneClasses =
    tone === 'indigo'
      ? 'bg-indigo-50 text-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-100 border-indigo-200/70 dark:border-indigo-900'
      : tone === 'emerald'
        ? 'bg-emerald-50 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100 border-emerald-200/70 dark:border-emerald-900'
        : tone === 'amber'
          ? 'bg-amber-50 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100 border-amber-200/70 dark:border-amber-900'
          : 'bg-slate-50 text-slate-900 dark:bg-slate-900/40 dark:text-slate-100 border-slate-200/70 dark:border-slate-700';

  return (
    <div className={`rounded-2xl border p-4 ${toneClasses}`}>
      <div className="text-xs font-semibold uppercase tracking-wide opacity-80">
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold">
        {loading ? '—' : (value ?? 0)}
      </div>
    </div>
  );
}

