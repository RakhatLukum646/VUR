import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuthStore } from '../store/useAuthStore';
import LoginPage from './LoginPage';

const loginUserMock = vi.fn();
const resendVerificationMock = vi.fn();

vi.mock('../services/authApi', () => ({
  loginUser: (...args: unknown[]) => loginUserMock(...args),
  resendVerification: (...args: unknown[]) => resendVerificationMock(...args),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<div>translator home</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    loginUserMock.mockReset();
    resendVerificationMock.mockReset();
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isBootstrapped: true,
      isBootstrapping: false,
    });
  });

  it('stores the authenticated user and navigates after login', async () => {
    const user = userEvent.setup();
    loginUserMock.mockResolvedValue({
      token_type: 'session',
      access_expires_in: 900,
      refresh_expires_in: 604800,
      user: {
        id: 'user-1',
        name: 'Test User',
        email: 'user@example.com',
        is_verified: true,
      },
    });

    renderPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'supersecret');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByText('translator home')).toBeInTheDocument();
    expect(useAuthStore.getState().user?.email).toBe('user@example.com');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('reveals second-factor controls when the API requests 2FA', async () => {
    const user = userEvent.setup();
    loginUserMock.mockRejectedValue(new Error('2FA code required'));

    renderPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'supersecret');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(
      await screen.findByText('Enter your authenticator code or use a recovery code.')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Authenticator' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Recovery code' })).toBeInTheDocument();
  });

  it('resends verification emails after a verification error', async () => {
    const user = userEvent.setup();
    loginUserMock.mockRejectedValue(new Error('Email verification required'));
    resendVerificationMock.mockResolvedValue({
      message: 'Verification email queued.',
    });

    renderPage();

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'supersecret');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));
    await user.click(
      await screen.findByRole('button', { name: 'Resend verification email' })
    );

    await waitFor(() => {
      expect(resendVerificationMock).toHaveBeenCalledWith('user@example.com');
    });
    expect(screen.getByText('Verification email queued.')).toBeInTheDocument();
  });
});
