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
    const [loginAttempts, setLoginAttempts] = useState<number>(3); // Intentos restantes (MAX_LOGIN_ATTEMPTS=3)
    const [accountLocked, setAccountLocked] = useState<boolean>(false); // Cuenta bloqueada
    const [lockedMinutes, setLockedMinutes] = useState<number>(0); // Minutos bloqueado

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
        setAccountLocked(false);

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

            // Reset attempts on successful login
            setLoginAttempts(3);

            return true;
        } catch (err: unknown) {
            // Get error detail from response
            const error = err as { response?: { data?: { detail?: string; remaining_attempts?: number; account_locked?: boolean; remaining_minutes?: number; role?: string; active_session_exists?: boolean } } };
            const detail = error?.response?.data?.detail || '';
            
            // Extract attempt information from error response
            let friendlyMessage = 'Error al iniciar sesión. Intente de nuevo.';
            let remainingAttempts = 3;
            let isLocked = false;
            let remainingMin = 0;
            let userRole = 'user';
            let activeSessionExists = false;

            // Extraer datos del response
            if (error?.response?.data) {
                const errorData = error.response.data;
                if (errorData.remaining_attempts !== undefined) {
                    remainingAttempts = errorData.remaining_attempts;
                    setLoginAttempts(remainingAttempts);
                }
                if (errorData.account_locked !== undefined) {
                    isLocked = errorData.account_locked;
                    setAccountLocked(isLocked);
                }
                if (errorData.remaining_minutes !== undefined) {
                    remainingMin = errorData.remaining_minutes;
                    setLockedMinutes(remainingMin);
                }
                if (errorData.role !== undefined) {
                    userRole = errorData.role;
                }
                if (errorData.active_session_exists !== undefined) {
                    activeSessionExists = errorData.active_session_exists;
                }
            }

            // Check for active session first
            if (activeSessionExists || detail.includes('está siendo usada')) {
                friendlyMessage = 'Esta sesión está siendo usada. Por favor desconéctese de la sesión antes de volver a querer entrar.';
                setError(friendlyMessage);
                return false;
            }

            // Translate to user-friendly messages según el rol
            if (detail.includes('Credenciales inválidas') || detail.includes('inválidas')) {
                if (isLocked) {
                    if (userRole === 'admin') {
                        friendlyMessage = `Le falta ${remainingMin} minuto(s) para desbloquear su cuenta.`;
                    } else {
                        friendlyMessage = `Debe contactar al administrador para desbloquear su cuenta.`;
                    }
                } else if (remainingAttempts <= 1) {
                    friendlyMessage = `⚠️ ADVERTENCIA: Este es su último intento. Si falla, su cuenta será bloqueada.`;
                } else {
                    friendlyMessage = `Usuario o contraseña incorrectos. ${remainingAttempts} intento(s) restante(s).`;
                }
            } else if (detail.includes('bloqueada') || detail.includes('Cuenta bloqueada')) {
                friendlyMessage = detail; // Keep lockout message as is
                setAccountLocked(true);
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
        loginAttempts,
        accountLocked,
        lockedMinutes,
        register,
        login,
        logout,
        setFaceVerified,
        updateUser,
        clearError,
    };
}
