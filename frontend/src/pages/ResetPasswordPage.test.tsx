import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ResetPasswordPage from './ResetPasswordPage';

const confirmPasswordResetMock = vi.fn();

vi.mock('../services/authApi', () => ({
  confirmPasswordReset: (...args: unknown[]) => confirmPasswordResetMock(...args),
}));

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    confirmPasswordResetMock.mockReset();
  });

  it('submits the reset token and new password', async () => {
    const user = userEvent.setup();
    confirmPasswordResetMock.mockResolvedValue({
      message: 'Password reset successfully',
    });

    render(
      <MemoryRouter initialEntries={['/reset-password?token=reset-token']}>
        <Routes>
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Routes>
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('New password'), 'newsecret');
    await user.type(screen.getByLabelText('Confirm password'), 'newsecret');
    await user.click(screen.getByRole('button', { name: 'Update password' }));

    await waitFor(() => {
      expect(confirmPasswordResetMock).toHaveBeenCalledWith(
        'reset-token',
        'newsecret'
      );
    });
    expect(screen.getByText('Password reset successfully')).toBeInTheDocument();
  });
});
