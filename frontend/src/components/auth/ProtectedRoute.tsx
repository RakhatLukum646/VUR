import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuthStore } from '../../store/useAuthStore';

interface Props {
  children: ReactNode;
  requireVerified?: boolean;
}

export default function ProtectedRoute({
  children,
  requireVerified = false,
}: Props) {
  const { isAuthenticated, isBootstrapped, user } = useAuthStore();

  if (!isBootstrapped) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireVerified && user && !user.is_verified) {
    return <Navigate to="/profile" replace />;
  }

  return <>{children}</>;
}
