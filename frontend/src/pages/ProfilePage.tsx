import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import {
  changePassword,
  enable2FA,
  getCurrentUser,
  logoutAllDevices,
  regenerateRecoveryCodes,
  setup2FA,
  updateProfileName,
} from '../services/authApi';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { logout, updateUser, user } = useAuthStore();

  const [name, setName] = useState(user?.name ?? '');
  const [profileMessage, setProfileMessage] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [securityMessage, setSecurityMessage] = useState('');
  const [twoFaMessage, setTwoFaMessage] = useState('');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [recoveryPassword, setRecoveryPassword] = useState('');

  const [twoFaSecret, setTwoFaSecret] = useState('');
  const [twoFaUrl, setTwoFaUrl] = useState('');
  const [twoFaCode, setTwoFaCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);

  const refreshProfile = async () => {
    const freshUser = await getCurrentUser();
    updateUser(freshUser);
    setName(freshUser.name);
  };

  useEffect(() => {
    let isActive = true;

    getCurrentUser()
      .then((freshUser) => {
        if (!isActive) {
          return;
        }

        updateUser(freshUser);
        setName(freshUser.name);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }

        logout();
        navigate('/login', { replace: true });
      });

    return () => {
      isActive = false;
    };
  }, [logout, navigate, updateUser]);

  const handleNameUpdate = async () => {
    setProfileMessage('');

    try {
      await updateProfileName(name);
      await refreshProfile();
      setProfileMessage('Name updated successfully.');
    } catch (error: unknown) {
      setProfileMessage(
        error instanceof Error ? error.message : 'Failed to update name'
      );
    }
  };

  const handlePasswordChange = async () => {
    setPasswordMessage('');

    try {
      const result = await changePassword(currentPassword, newPassword);
      setPasswordMessage(result.message);
      setCurrentPassword('');
      setNewPassword('');
      logout();
      navigate('/login', { replace: true });
    } catch (error: unknown) {
      setPasswordMessage(
        error instanceof Error ? error.message : 'Failed to change password'
      );
    }
  };

  const handleLogoutAllDevices = async () => {
    setSecurityMessage('');

    try {
      const result = await logoutAllDevices();
      setSecurityMessage(result.message);
      logout();
      navigate('/login', { replace: true });
    } catch (error: unknown) {
      setSecurityMessage(
        error instanceof Error ? error.message : 'Failed to close sessions'
      );
    }
  };

  const handleSetup2FA = async () => {
    setTwoFaMessage('');

    try {
      const result = await setup2FA();
      setTwoFaSecret(result.secret);
      setTwoFaUrl(result.otp_auth_url);
      setRecoveryCodes([]);
      setTwoFaMessage(
        '2FA secret generated. Scan it in your authenticator and confirm below.'
      );
    } catch (error: unknown) {
      setTwoFaMessage(
        error instanceof Error ? error.message : 'Failed to setup 2FA'
      );
    }
  };

  const handleEnable2FA = async () => {
    setTwoFaMessage('');

    try {
      const result = await enable2FA(twoFaCode);
      setRecoveryCodes(result.recovery_codes);
      setTwoFaCode('');
      setTwoFaMessage(result.message);
      await refreshProfile();
    } catch (error: unknown) {
      setTwoFaMessage(
        error instanceof Error ? error.message : 'Failed to enable 2FA'
      );
    }
  };

  const handleRegenerateRecoveryCodes = async () => {
    setTwoFaMessage('');

    try {
      const result = await regenerateRecoveryCodes(recoveryPassword);
      setRecoveryCodes(result.recovery_codes);
      setRecoveryPassword('');
      setTwoFaMessage(result.message);
    } catch (error: unknown) {
      setTwoFaMessage(
        error instanceof Error
          ? error.message
          : 'Failed to regenerate recovery codes'
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Profile</h1>

          <div className="space-y-2 text-gray-700">
            <p>
              <span className="font-semibold">Email:</span> {user?.email}
            </p>
            <p>
              <span className="font-semibold">Email verified:</span>{' '}
              {user?.is_verified ? 'Yes' : 'No'}
            </p>
            <p>
              <span className="font-semibold">2FA enabled:</span>{' '}
              {user?.two_factor_enabled ? 'Yes' : 'No'}
            </p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Change Name</h2>
          <div className="space-y-4">
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
            />
            <button
              onClick={handleNameUpdate}
              className="px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
            >
              Save name
            </button>
            {profileMessage && (
              <p className="text-sm text-gray-600">{profileMessage}</p>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Change Password
          </h2>
          <div className="space-y-4">
            <input
              type="password"
              placeholder="Current password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
            />
            <input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
            />
            <button
              onClick={handlePasswordChange}
              className="px-5 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              Change password
            </button>
            <p className="text-sm text-gray-500">
              Password changes close all active sessions, including this one.
            </p>
            {passwordMessage && (
              <p className="text-sm text-gray-600">{passwordMessage}</p>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Session Security
          </h2>
          <div className="space-y-4">
            <p className="text-gray-700">
              Sessions are stored as secure HTTP-only cookies. Use this control if
              you signed in on another device and want to invalidate every session.
            </p>
            <button
              onClick={handleLogoutAllDevices}
              className="px-5 py-3 rounded-lg bg-amber-500 hover:bg-amber-600 text-white"
            >
              Log out all devices
            </button>
            {securityMessage && (
              <p className="text-sm text-gray-600">{securityMessage}</p>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Two-Factor Authentication
          </h2>
          <div className="space-y-4">
            {!user?.two_factor_enabled && (
              <>
                <button
                  onClick={handleSetup2FA}
                  className="px-5 py-3 rounded-lg bg-purple-600 hover:bg-purple-700 text-white"
                >
                  Setup 2FA
                </button>

                {twoFaSecret && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
                    <p className="text-sm text-gray-700">
                      Add this secret to your authenticator:
                    </p>
                    <p className="font-mono text-sm break-all text-gray-900">
                      {twoFaSecret}
                    </p>
                    <p className="text-xs text-gray-500 break-all">{twoFaUrl}</p>
                  </div>
                )}

                {twoFaSecret && (
                  <>
                    <input
                      type="text"
                      placeholder="Enter 6-digit code"
                      value={twoFaCode}
                      onChange={(event) =>
                        setTwoFaCode(
                          event.target.value.replace(/\D/g, '').slice(0, 6)
                        )
                      }
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
                    />
                    <button
                      onClick={handleEnable2FA}
                      className="px-5 py-3 rounded-lg bg-green-600 hover:bg-green-700 text-white"
                    >
                      Enable 2FA
                    </button>
                  </>
                )}
              </>
            )}

            {user?.two_factor_enabled && (
              <>
                <p className="text-green-700">2FA is enabled on your account.</p>
                <input
                  type="password"
                  placeholder="Current password to regenerate recovery codes"
                  value={recoveryPassword}
                  onChange={(event) => setRecoveryPassword(event.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
                />
                <button
                  onClick={handleRegenerateRecoveryCodes}
                  className="px-5 py-3 rounded-lg bg-slate-800 hover:bg-slate-900 text-white"
                >
                  Regenerate recovery codes
                </button>
              </>
            )}

            {recoveryCodes.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm font-medium text-amber-900 mb-2">
                  Store these recovery codes offline. Each code works once.
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {recoveryCodes.map((code) => (
                    <code
                      key={code}
                      className="rounded-md bg-white px-3 py-2 text-sm text-gray-900"
                    >
                      {code}
                    </code>
                  ))}
                </div>
              </div>
            )}

            {twoFaMessage && <p className="text-sm text-gray-600">{twoFaMessage}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
