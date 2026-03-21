import { useState } from 'react';
import { Hand } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { confirmPasswordReset } from '../services/authApi';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get('token');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState(
    token ? '' : 'Missing password reset token.'
  );
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!token) {
      setMessage('Missing password reset token.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage('Passwords do not match.');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const result = await confirmPasswordReset(token, newPassword);
      setMessage(result.message);
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: unknown) {
      setMessage(
        error instanceof Error ? error.message : 'Failed to reset password'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Hand className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Choose a new password</h1>
            <p className="text-sm text-gray-500">
              This resets the account and invalidates existing sessions.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="reset-new-password"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              New password
            </label>
            <input
              id="reset-new-password"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              autoComplete="new-password"
              required
              minLength={6}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 bg-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter a new password"
            />
          </div>

          <div>
            <label
              htmlFor="reset-confirm-password"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Confirm password
            </label>
            <input
              id="reset-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              autoComplete="new-password"
              required
              minLength={6}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 bg-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Repeat the new password"
            />
          </div>

          {message && (
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !token}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? 'Updating password...' : 'Update password'}
          </button>
        </form>

        <div className="mt-5 text-center text-sm text-gray-600">
          <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
