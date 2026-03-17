import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { verifyEmail } from '../services/authApi';

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const [message, setMessage] = useState(() =>
    params.get('token') ? 'Verifying email...' : 'Missing verification token'
  );

  useEffect(() => {
    const token = params.get('token');
    if (!token) return;

    verifyEmail(token)
      .then((result) => setMessage(result.message))
      .catch((err: unknown) =>
        setMessage(err instanceof Error ? err.message : 'Verification failed')
      );
  }, [params]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm max-w-md w-full">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Email Verification</h1>
        <p className="text-gray-700">{message}</p>
      </div>
    </div>
  );
}