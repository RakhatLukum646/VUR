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
  } = useAuthStore();

  useEffect(() => {
    if (isBootstrapped || isBootstrapping) {
      return;
    }

    beginBootstrap();
    bootstrapSession()
      .then((user) => completeBootstrap(user))
      .catch(() => completeBootstrap(null));
  }, [
    beginBootstrap,
    completeBootstrap,
    isBootstrapped,
    isBootstrapping,
  ]);

  if (!isBootstrapped) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="rounded-2xl border border-gray-200 bg-white px-6 py-5 text-sm text-gray-600 shadow-sm">
          Checking session…
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
