import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { bootstrapSession } from '../../services/authApi';
import { useAuthStore } from '../../store/useAuthStore';

interface Props {
  children: ReactNode;
}

export default function AuthBootstrap({ children }: Props) {
  const {
    isBootstrapped,
    isBootstrapping,
    beginBootstrap,
    completeBootstrap,
    setAccessToken,
  } = useAuthStore();

  useEffect(() => {
    if (isBootstrapped || isBootstrapping) {
      return;
    }

    beginBootstrap();
    bootstrapSession()
      .then((session) => {
        if (session) {
          setAccessToken(session.access_token);
          completeBootstrap(session.user);
        } else {
          completeBootstrap(null);
        }
      })
      .catch(() => completeBootstrap(null));
  }, [
    beginBootstrap,
    completeBootstrap,
    setAccessToken,
    isBootstrapped,
    isBootstrapping,
  ]);

  if (!isBootstrapped) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center px-4">
        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 py-5 text-sm text-gray-600 dark:text-gray-300 shadow-sm">
          Checking session…
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
