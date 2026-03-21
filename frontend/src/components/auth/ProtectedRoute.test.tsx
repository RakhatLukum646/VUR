import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { useAuthStore } from '../../store/useAuthStore';
import ProtectedRoute from './ProtectedRoute';

function renderRoute(requireVerified = false) {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute requireVerified={requireVerified}>
              <div>protected content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>login page</div>} />
        <Route path="/profile" element={<div>profile page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to login', () => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isBootstrapped: true,
      isBootstrapping: false,
    });

    renderRoute();

    expect(screen.getByText('login page')).toBeInTheDocument();
  });

  it('renders children for authenticated users', () => {
    useAuthStore.setState({
      user: {
        id: 'user-1',
        name: 'Test User',
        email: 'user@example.com',
        is_verified: true,
      },
      isAuthenticated: true,
      isBootstrapped: true,
      isBootstrapping: false,
    });

    renderRoute();

    expect(screen.getByText('protected content')).toBeInTheDocument();
  });

  it('redirects unverified users when verification is required', () => {
    useAuthStore.setState({
      user: {
        id: 'user-1',
        name: 'Test User',
        email: 'user@example.com',
        is_verified: false,
      },
      isAuthenticated: true,
      isBootstrapped: true,
      isBootstrapping: false,
    });

    renderRoute(true);

    expect(screen.getByText('profile page')).toBeInTheDocument();
  });
});
