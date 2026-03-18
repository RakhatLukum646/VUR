import { useState } from 'react';
import { Hand } from 'lucide-react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { loginUser, resendVerification } from '../services/authApi';
import { useAuthStore } from '../store/useAuthStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isBootstrapped, login } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twofaCode, setTwofaCode] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [requiresSecondFactor, setRequiresSecondFactor] = useState(false);
  const [useRecoveryCode, setUseRecoveryCode] = useState(false);
  const [canResendVerification, setCanResendVerification] = useState(false);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  if (isBootstrapped && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const result = await loginUser({
        email,
        password,
        twofa_code:
          requiresSecondFactor && !useRecoveryCode ? twofaCode : undefined,
        recovery_code:
          requiresSecondFactor && useRecoveryCode ? recoveryCode : undefined,
      });

      login(result.user);
      navigate('/');
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : 'Login failed';

      if (detail.toLowerCase().includes('2fa code required')) {
        setRequiresSecondFactor(true);
        setCanResendVerification(false);
        setMessage('Enter your authenticator code or use a recovery code.');
      } else if (detail.toLowerCase().includes('email verification required')) {
        setCanResendVerification(true);
        setRequiresSecondFactor(false);
        setMessage('Verify your email before signing in.');
      } else {
        setCanResendVerification(false);
        setMessage(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerification = async () => {
    if (!email) {
      setMessage('Enter your email address first.');
      return;
    }

    setResending(true);
    try {
      const result = await resendVerification(email);
      setMessage(result.message);
    } catch (error: unknown) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to resend verification email'
      );
    } finally {
      setResending(false);
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
            <h1 className="text-xl font-bold text-gray-900">
              AI Sign Language Translator
            </h1>
            <p className="text-sm text-gray-500">Sign in with a secure session</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="login-email"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Email
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your email"
              autoComplete="email"
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 bg-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                htmlFor="login-password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <Link
                to="/forgot-password"
                className="text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 bg-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {requiresSecondFactor && (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-4">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setUseRecoveryCode(false)}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    !useRecoveryCode
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300'
                  }`}
                >
                  Authenticator
                </button>
                <button
                  type="button"
                  onClick={() => setUseRecoveryCode(true)}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    useRecoveryCode
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300'
                  }`}
                >
                  Recovery code
                </button>
              </div>

              {!useRecoveryCode ? (
                <div>
                  <label
                    htmlFor="login-twofa-code"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    2FA Code
                  </label>
                  <input
                    id="login-twofa-code"
                    type="text"
                    value={twofaCode}
                    onChange={(event) =>
                      setTwofaCode(
                        event.target.value.replace(/\D/g, '').slice(0, 6)
                      )
                    }
                    placeholder="Enter 6-digit code"
                    inputMode="numeric"
                    maxLength={6}
                    className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 bg-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              ) : (
                <div>
                  <label
                    htmlFor="login-recovery-code"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Recovery Code
                  </label>
                  <input
                    id="login-recovery-code"
                    type="text"
                    value={recoveryCode}
                    onChange={(event) =>
                      setRecoveryCode(event.target.value.toUpperCase())
                    }
                    placeholder="ABCD-1234"
                    autoCapitalize="characters"
                    className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 bg-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              )}
            </div>
          )}

          {message && (
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading
              ? 'Signing in...'
              : requiresSecondFactor
                ? 'Verify and sign in'
                : 'Sign in'}
          </button>
        </form>

        {canResendVerification && (
          <button
            type="button"
            onClick={handleResendVerification}
            disabled={resending}
            className="mt-4 w-full rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800 transition-colors hover:bg-amber-100 disabled:opacity-60"
          >
            {resending ? 'Sending verification email...' : 'Resend verification email'}
          </button>
        )}

        <div className="text-center text-sm text-gray-600 mt-5">
          Don&apos;t have an account?{' '}
          <Link
            to="/signup"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
