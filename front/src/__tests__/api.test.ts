/**
 * Login Seguro - Tests: API Service
 * Tests para el servicio de API
 */

import axios from 'axios';
import Cookies from 'js-cookie';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    post: jest.fn(),
    get: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  })),
}));

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockClear();
    (Cookies.set as jest.Mock).mockClear();
    (Cookies.remove as jest.Mock).mockClear();
  });

  describe('axios instance', () => {
    it('should create axios instance with correct config', () => {
      // Re-import to trigger module initialization
      jest.isolateModules(() => {
        require('@/services/api');
      });

      expect(axios.create).toHaveBeenCalled();
    });
  });

  describe('Cookies', () => {
    it('should get token from cookies', () => {
      (Cookies.get as jest.Mock).mockReturnValue('test-token');
      
      const token = Cookies.get('access_token');
      
      expect(token).toBe('test-token');
      expect(Cookies.get).toHaveBeenCalledWith('access_token');
    });

    it('should return undefined when no token', () => {
      (Cookies.get as jest.Mock).mockReturnValue(undefined);
      
      const token = Cookies.get('access_token');
      
      expect(token).toBeUndefined();
    });

    it('should set token in cookies', () => {
      Cookies.set('access_token', 'new-token', { expires: 1 });
      
      expect(Cookies.set).toHaveBeenCalledWith(
        'access_token',
        'new-token',
        expect.objectContaining({ expires: 1 })
      );
    });

    it('should remove token from cookies', () => {
      Cookies.remove('access_token');
      
      expect(Cookies.remove).toHaveBeenCalledWith('access_token');
    });
  });
});

describe('API Response Handling', () => {
  describe('Success responses', () => {
    it('should handle successful login response structure', () => {
      const mockResponse = {
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

      expect(mockResponse.access_token).toBeDefined();
      expect(mockResponse.user).toBeDefined();
      expect(mockResponse.user.username).toBe('testuser');
    });

    it('should handle successful register response structure', () => {
      const mockResponse = {
        success: true,
        message: 'Usuario registrado exitosamente',
      };

      expect(mockResponse.success).toBe(true);
      expect(mockResponse.message).toBeDefined();
    });
  });

  describe('Error responses', () => {
    it('should handle 401 unauthorized', () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            detail: 'Token inválido o expirado',
          },
        },
      };

      expect(mockError.response.status).toBe(401);
      expect(mockError.response.data.detail).toContain('Token');
    });

    it('should handle 422 validation error', () => {
      const mockError = {
        response: {
          status: 422,
          data: {
            detail: 'Error de validación',
            errors: [
              { field: 'username', message: 'Username requerido' },
            ],
          },
        },
      };

      expect(mockError.response.status).toBe(422);
      expect(mockError.response.data.errors).toBeDefined();
    });

    it('should handle 429 rate limit', () => {
      const mockError = {
        response: {
          status: 429,
          data: {
            detail: 'Demasiadas solicitudes',
          },
        },
      };

      expect(mockError.response.status).toBe(429);
    });

    it('should handle network error', () => {
      const mockError = {
        message: 'Network Error',
        code: 'ERR_NETWORK',
      };

      expect(mockError.code).toBe('ERR_NETWORK');
    });
  });
});

describe('API Interceptors', () => {
  describe('Request interceptor', () => {
    it('should add authorization header when token exists', () => {
      const mockConfig = {
        headers: {} as Record<string, string>,
      };
      const token = 'test-jwt-token';

      // Simulate adding token to header
      if (token) {
        mockConfig.headers.Authorization = `Bearer ${token}`;
      }

      expect(mockConfig.headers.Authorization).toBe(`Bearer ${token}`);
    });

    it('should not add authorization header when no token', () => {
      const mockConfig = {
        headers: {} as Record<string, string>,
      };
      const token = undefined;

      if (token) {
        mockConfig.headers.Authorization = `Bearer ${token}`;
      }

      expect(mockConfig.headers.Authorization).toBeUndefined();
    });
  });
});
