'use client';

import { useState, useCallback, useEffect } from 'react';
import Cookies from 'js-cookie';
import { AuthState, User, LoginData, RegisterData } from '@/types';
import { authApi } from '@/services/api';

const initialState: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
    requiresFaceRegistration: false,
    requiresFaceVerification: false,
    faceVerified: false,
};

export function useAuth() {
    const [authState, setAuthState] = useState<AuthState>(initialState);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Check for existing token on mount
    useEffect(() => {
        const token = Cookies.get('access_token');
        if (token) {
            // Token exists, try to get user info
            setAuthState((prev) => ({
                ...prev,
                isAuthenticated: true,
                token,
            }));
        }
    }, []);

    const register = useCallback(async (data: RegisterData): Promise<boolean> => {
        setLoading(true);
        setError(null);

        try {
            await authApi.register(data);
            return true;
        } catch (err: unknown) {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';

            // Translate to user-friendly messages
            let friendlyMessage = 'Error al crear la cuenta. Intente de nuevo.';

            if (detail.includes('username') || detail.includes('usuario ya está')) {
                friendlyMessage = 'Este nombre de usuario ya está en uso';
            } else if (detail.includes('email') || detail.includes('correo')) {
                friendlyMessage = 'Este correo electrónico ya está registrado';
            } else if (detail.includes('contraseña') || detail.includes('password')) {
                friendlyMessage = 'La contraseña no cumple los requisitos de seguridad';
            } else if (detail.includes('conexión') || detail.includes('base de datos')) {
                friendlyMessage = 'Error de conexión. Intente más tarde.';
            }

            setError(friendlyMessage);
            return false;
        } finally {
            setLoading(false);
        }
    }, []);

    const login = useCallback(async (data: LoginData): Promise<boolean> => {
        setLoading(true);
        setError(null);

        try {
            const response = await authApi.login(data);

            setAuthState({
                isAuthenticated: true,
                user: response.user,
                token: response.access_token,
                requiresFaceRegistration: response.requires_face_registration,
                requiresFaceVerification: response.requires_face_verification,
                faceVerified: false,
            });

            return true;
        } catch (err: unknown) {
            // Get error detail from response
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';

            // Translate to user-friendly messages
            let friendlyMessage = 'Error al iniciar sesión. Intente de nuevo.';

            if (detail.includes('Credenciales inválidas') || detail.includes('inválidas')) {
                friendlyMessage = 'Usuario o contraseña incorrectos';
            } else if (detail.includes('bloqueada') || detail.includes('Cuenta bloqueada')) {
                friendlyMessage = detail; // Keep lockout message as is
            } else if (detail.includes('no encontrado')) {
                friendlyMessage = 'Usuario o contraseña incorrectos';
            } else if (detail.includes('conexión') || detail.includes('base de datos')) {
                friendlyMessage = 'Error de conexión. Intente más tarde.';
            }

            setError(friendlyMessage);
            return false;
        } finally {
            setLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        authApi.logout();
        setAuthState(initialState);
    }, []);

    const setFaceVerified = useCallback(() => {
        setAuthState((prev) => ({
            ...prev,
            faceVerified: true,
            requiresFaceVerification: false,
            requiresFaceRegistration: false,
        }));
    }, []);

    const updateUser = useCallback((user: User) => {
        setAuthState((prev) => ({
            ...prev,
            user,
            requiresFaceRegistration: !user.face_registered,
            requiresFaceVerification: user.face_registered,
        }));
    }, []);

    const clearError = useCallback(() => {
        setError(null);
    }, []);

    return {
        ...authState,
        loading,
        error,
        register,
        login,
        logout,
        setFaceVerified,
        updateUser,
        clearError,
    };
}
