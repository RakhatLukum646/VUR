import { useEffect, useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import {
  getCurrentUser,
  updateProfileName,
  changePassword,
  resendVerification,
  setup2FA,
  enable2FA,
} from '../services/authApi';

export default function ProfilePage() {
  const { user, token, login } = useAuthStore();

  const [name, setName] = useState(user?.name || '');
  const [profileMessage, setProfileMessage] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [verificationMessage, setVerificationMessage] = useState('');
  const [twoFaMessage, setTwoFaMessage] = useState('');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [twoFaSecret, setTwoFaSecret] = useState('');
  const [twoFaUrl, setTwoFaUrl] = useState('');
  const [twoFaCode, setTwoFaCode] = useState('');

  useEffect(() => {
    const loadProfile = async () => {
      if (!token) return;
      try {
        const freshUser = await getCurrentUser(token);
        login(freshUser, token);
        setName(freshUser.name);
      } catch (err) {
        console.error(err);
      }
    };

    loadProfile();
  }, [token, login]);

  const handleNameUpdate = async () => {
    if (!token) return;
    try {
      await updateProfileName(token, name);
      const freshUser = await getCurrentUser(token);
      login(freshUser, token);
      setProfileMessage('Name updated successfully');
    } catch (err: unknown) {
      setProfileMessage(err instanceof Error ? err.message : 'Failed to update name');
    }
  };

  const handlePasswordChange = async () => {
    if (!token) return;
    try {
      await changePassword(token, currentPassword, newPassword);
      setPasswordMessage('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: unknown) {
      setPasswordMessage(err instanceof Error ? err.message : 'Failed to change password');
    }
  };

  const handleResendVerification = async () => {
    if (!token) return;
    try {
      const result = await resendVerification(token);
      setVerificationMessage(result.message);
    } catch (err: unknown) {
      setVerificationMessage(err instanceof Error ? err.message : 'Failed to resend verification');
    }
  };

  const handleSetup2FA = async () => {
    if (!token) return;
    try {
      const result = await setup2FA(token);
      setTwoFaSecret(result.secret);
      setTwoFaUrl(result.otp_auth_url);
      setTwoFaMessage('2FA secret generated. Add it to Google Authenticator.');
    } catch (err: unknown) {
      setTwoFaMessage(err instanceof Error ? err.message : 'Failed to setup 2FA');
    }
  };

  const handleEnable2FA = async () => {
    if (!token) return;
    try {
      const result = await enable2FA(token, twoFaCode);
      setTwoFaMessage(result.message);
      const freshUser = await getCurrentUser(token);
      login(freshUser, token);
    } catch (err: unknown) {
      setTwoFaMessage(err instanceof Error ? err.message : 'Failed to enable 2FA');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Profile</h1>

          <div className="space-y-2 text-gray-700">
            <p><span className="font-semibold">Email:</span> {user?.email}</p>
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
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
            />
            <button
              onClick={handleNameUpdate}
              className="px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
            >
              Save Name
            </button>
            {profileMessage && <p className="text-sm text-gray-600">{profileMessage}</p>}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Change Password</h2>
          <div className="space-y-4">
            <input
              type="password"
              placeholder="Current password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
            />
            <input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
            />
            <button
              onClick={handlePasswordChange}
              className="px-5 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              Change Password
            </button>
            {passwordMessage && <p className="text-sm text-gray-600">{passwordMessage}</p>}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Email Verification</h2>
          <div className="space-y-4">
            {!user?.is_verified ? (
              <>
                <p className="text-gray-700">
                  Your email is not verified yet.
                </p>
                <button
                  onClick={handleResendVerification}
                  className="px-5 py-3 rounded-lg bg-amber-500 hover:bg-amber-600 text-white"
                >
                  Resend Verification Email
                </button>
              </>
            ) : (
              <p className="text-green-700">Your email is verified.</p>
            )}
            {verificationMessage && (
              <p className="text-sm text-gray-600">{verificationMessage}</p>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Two-Factor Authentication</h2>
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
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-700 mb-2">
                      Add this secret to Google Authenticator:
                    </p>
                    <p className="font-mono text-sm break-all text-gray-900">{twoFaSecret}</p>
                    <p className="text-xs text-gray-500 mt-2 break-all">{twoFaUrl}</p>
                  </div>
                )}

                {twoFaSecret && (
                  <>
                    <input
                      type="text"
                      placeholder="Enter 6-digit code"
                      value={twoFaCode}
                      onChange={(e) => setTwoFaCode(e.target.value)}
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
              <p className="text-green-700">2FA is enabled on your account.</p>
            )}

            {twoFaMessage && <p className="text-sm text-gray-600">{twoFaMessage}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}