/**
 * Login Seguro - Tests: Types
 * Tests para las definiciones de tipos TypeScript
 */

import {
  User,
  LoginResponse,
  MessageResponse,
  RegisterData,
  LoginData,
  FaceData,
  AuthState,
} from '@/types';

describe('Types', () => {
  describe('User', () => {
    it('should have required properties', () => {
      const user: User = {
        id: 1,
        username: 'testuser',
        face_registered: false,
      };

      expect(user.id).toBe(1);
      expect(user.username).toBe('testuser');
      expect(user.face_registered).toBe(false);
    });

    it('should allow optional email', () => {
      const userWithEmail: User = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        face_registered: true,
      };

      expect(userWithEmail.email).toBe('test@example.com');
    });

    it('should allow undefined email', () => {
      const userWithoutEmail: User = {
        id: 1,
        username: 'testuser',
        face_registered: false,
      };

      expect(userWithoutEmail.email).toBeUndefined();
    });
  });

  describe('LoginResponse', () => {
    it('should have all required properties', () => {
      const response: LoginResponse = {
        access_token: 'token123',
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

      expect(response.access_token).toBe('token123');
      expect(response.token_type).toBe('bearer');
      expect(response.expires_in).toBe(1800);
      expect(response.user).toBeDefined();
      expect(response.requires_face_registration).toBe(true);
      expect(response.requires_face_verification).toBe(false);
    });
  });

  describe('MessageResponse', () => {
    it('should have success and message', () => {
      const response: MessageResponse = {
        success: true,
        message: 'Operation successful',
      };

      expect(response.success).toBe(true);
      expect(response.message).toBe('Operation successful');
    });

    it('should allow optional data', () => {
      const response: MessageResponse = {
        success: true,
        message: 'Operation successful',
        data: { key: 'value' },
      };

      expect(response.data).toEqual({ key: 'value' });
    });
  });

  describe('RegisterData', () => {
    it('should have required username and password', () => {
      const data: RegisterData = {
        username: 'newuser',
        password: 'SecurePass123!',
      };

      expect(data.username).toBe('newuser');
      expect(data.password).toBe('SecurePass123!');
    });

    it('should allow optional email', () => {
      const data: RegisterData = {
        username: 'newuser',
        password: 'SecurePass123!',
        email: 'new@example.com',
      };

      expect(data.email).toBe('new@example.com');
    });
  });

  describe('LoginData', () => {
    it('should have username and password', () => {
      const data: LoginData = {
        username: 'testuser',
        password: 'password123',
      };

      expect(data.username).toBe('testuser');
      expect(data.password).toBe('password123');
    });
  });

  describe('FaceData', () => {
    it('should have image_data', () => {
      const data: FaceData = {
        image_data: 'data:image/jpeg;base64,/9j/...',
      };

      expect(data.image_data).toBeDefined();
      expect(data.image_data.startsWith('data:image')).toBe(true);
    });
  });

  describe('AuthState', () => {
    it('should have all required properties', () => {
      const state: AuthState = {
        isAuthenticated: false,
        user: null,
        token: null,
        requiresFaceRegistration: false,
        requiresFaceVerification: false,
        faceVerified: false,
      };

      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.requiresFaceRegistration).toBe(false);
      expect(state.requiresFaceVerification).toBe(false);
      expect(state.faceVerified).toBe(false);
    });

    it('should allow authenticated state with user', () => {
      const state: AuthState = {
        isAuthenticated: true,
        user: {
          id: 1,
          username: 'testuser',
          face_registered: true,
        },
        token: 'token123',
        requiresFaceRegistration: false,
        requiresFaceVerification: true,
        faceVerified: false,
      };

      expect(state.isAuthenticated).toBe(true);
      expect(state.user).not.toBeNull();
      expect(state.token).toBe('token123');
    });
  });
});
