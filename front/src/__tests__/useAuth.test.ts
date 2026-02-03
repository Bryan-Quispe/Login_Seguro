/**
 * Login Seguro - Tests: useAuth Hook
 * Tests para el hook de autenticación
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import Cookies from 'js-cookie';

// Mock the api module
jest.mock('@/services/api', () => ({
  authApi: {
    register: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
  },
}));

import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/services/api';

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue(undefined);
    (Cookies.set as jest.Mock).mockClear();
    (Cookies.remove as jest.Mock).mockClear();
  });

  describe('Initial state', () => {
    it('should have correct initial state without token', () => {
      const { result } = renderHook(() => useAuth());

      expect(result.current.authState.isAuthenticated).toBe(false);
      expect(result.current.authState.user).toBeNull();
      expect(result.current.authState.token).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should detect existing token on mount', () => {
      (Cookies.get as jest.Mock).mockReturnValue('existing-token');

      const { result } = renderHook(() => useAuth());

      // After effect runs
      waitFor(() => {
        expect(result.current.authState.isAuthenticated).toBe(true);
        expect(result.current.authState.token).toBe('existing-token');
      });
    });
  });

  describe('register', () => {
    it('should call authApi.register with correct data', async () => {
      const mockRegister = authApi.register as jest.Mock;
      mockRegister.mockResolvedValue({ success: true, message: 'Registered' });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.register({
          username: 'newuser',
          password: 'SecurePass123!',
          email: 'new@example.com',
        });
      });

      expect(mockRegister).toHaveBeenCalledWith({
        username: 'newuser',
        password: 'SecurePass123!',
        email: 'new@example.com',
      });
    });

    it('should return true on successful registration', async () => {
      const mockRegister = authApi.register as jest.Mock;
      mockRegister.mockResolvedValue({ success: true, message: 'Registered' });

      const { result } = renderHook(() => useAuth());

      let success: boolean = false;
      await act(async () => {
        success = await result.current.register({
          username: 'newuser',
          password: 'SecurePass123!',
        });
      });

      expect(success).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should return false and set error on failed registration', async () => {
      const mockRegister = authApi.register as jest.Mock;
      mockRegister.mockRejectedValue({
        response: {
          data: {
            detail: 'usuario ya está registrado',
          },
        },
      });

      const { result } = renderHook(() => useAuth());

      let success: boolean = true;
      await act(async () => {
        success = await result.current.register({
          username: 'existinguser',
          password: 'SecurePass123!',
        });
      });

      expect(success).toBe(false);
      expect(result.current.error).toBeDefined();
    });

    it('should set loading state during registration', async () => {
      const mockRegister = authApi.register as jest.Mock;
      let resolvePromise: (value: unknown) => void;
      mockRegister.mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      const { result } = renderHook(() => useAuth());

      // Start registration
      let registerPromise: Promise<boolean>;
      act(() => {
        registerPromise = result.current.register({
          username: 'newuser',
          password: 'SecurePass123!',
        });
      });

      // Should be loading
      expect(result.current.loading).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolvePromise!({ success: true, message: 'Registered' });
        await registerPromise;
      });

      // Should no longer be loading
      expect(result.current.loading).toBe(false);
    });
  });

  describe('login', () => {
    const mockLoginResponse = {
      access_token: 'jwt-token',
      token_type: 'bearer',
      expires_in: 1800,
      user: {
        id: 1,
        username: 'testuser',
        face_registered: false,
      },
      requires_face_registration: true,
      requires_face_verification: false,
    };

    it('should call authApi.login with correct data', async () => {
      const mockLogin = authApi.login as jest.Mock;
      mockLogin.mockResolvedValue(mockLoginResponse);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'password123',
        });
      });

      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });

    it('should update auth state on successful login', async () => {
      const mockLogin = authApi.login as jest.Mock;
      mockLogin.mockResolvedValue(mockLoginResponse);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'password123',
        });
      });

      expect(result.current.authState.isAuthenticated).toBe(true);
      expect(result.current.authState.user).toEqual(mockLoginResponse.user);
      expect(result.current.authState.token).toBe(mockLoginResponse.access_token);
      expect(result.current.authState.requiresFaceRegistration).toBe(true);
    });

    it('should return true on successful login', async () => {
      const mockLogin = authApi.login as jest.Mock;
      mockLogin.mockResolvedValue(mockLoginResponse);

      const { result } = renderHook(() => useAuth());

      let success: boolean = false;
      await act(async () => {
        success = await result.current.login({
          username: 'testuser',
          password: 'password123',
        });
      });

      expect(success).toBe(true);
    });

    it('should return false on failed login', async () => {
      const mockLogin = authApi.login as jest.Mock;
      mockLogin.mockRejectedValue({
        response: {
          data: {
            detail: 'Credenciales inválidas',
          },
        },
      });

      const { result } = renderHook(() => useAuth());

      let success: boolean = true;
      await act(async () => {
        success = await result.current.login({
          username: 'testuser',
          password: 'wrongpassword',
        });
      });

      expect(success).toBe(false);
    });

    it('should handle account locked error', async () => {
      const mockLogin = authApi.login as jest.Mock;
      mockLogin.mockRejectedValue({
        response: {
          data: {
            detail: 'Cuenta bloqueada',
            account_locked: true,
            remaining_minutes: 15,
          },
        },
      });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login({
          username: 'lockeduser',
          password: 'password123',
        });
      });

      expect(result.current.accountLocked).toBe(true);
    });

    it('should track remaining login attempts', async () => {
      const mockLogin = authApi.login as jest.Mock;
      mockLogin.mockRejectedValue({
        response: {
          data: {
            detail: 'Credenciales inválidas',
            remaining_attempts: 2,
          },
        },
      });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'wrongpassword',
        });
      });

      expect(result.current.loginAttempts).toBe(2);
    });
  });

  describe('logout', () => {
    it('should call authApi.logout', async () => {
      const mockLogout = authApi.logout as jest.Mock;
      mockLogout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.logout();
      });

      expect(mockLogout).toHaveBeenCalled();
    });

    it('should reset auth state on logout', async () => {
      const mockLogin = authApi.login as jest.Mock;
      const mockLogout = authApi.logout as jest.Mock;
      mockLogin.mockResolvedValue({
        access_token: 'jwt-token',
        token_type: 'bearer',
        expires_in: 1800,
        user: { id: 1, username: 'testuser', face_registered: false },
        requires_face_registration: false,
        requires_face_verification: false,
      });
      mockLogout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth());

      // First login
      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'password123',
        });
      });

      expect(result.current.authState.isAuthenticated).toBe(true);

      // Then logout
      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.authState.isAuthenticated).toBe(false);
      expect(result.current.authState.user).toBeNull();
      expect(result.current.authState.token).toBeNull();
    });
  });

  describe('Error handling', () => {
    it('should translate username exists error', async () => {
      const mockRegister = authApi.register as jest.Mock;
      mockRegister.mockRejectedValue({
        response: {
          data: {
            detail: 'username already exists',
          },
        },
      });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.register({
          username: 'existinguser',
          password: 'SecurePass123!',
        });
      });

      expect(result.current.error).toContain('usuario');
    });

    it('should translate email exists error', async () => {
      const mockRegister = authApi.register as jest.Mock;
      mockRegister.mockRejectedValue({
        response: {
          data: {
            detail: 'email already registered',
          },
        },
      });

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.register({
          username: 'newuser',
          password: 'SecurePass123!',
          email: 'existing@example.com',
        });
      });

      expect(result.current.error).toContain('correo');
    });
  });
});
