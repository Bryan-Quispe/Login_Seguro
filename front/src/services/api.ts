import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';
import { LoginResponse, MessageResponse, RegisterData, LoginData, FaceData } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 seconds for face processing
});

// Request interceptor to add JWT token
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = Cookies.get('access_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Only redirect if not already on auth pages and has a token
            const isAuthPage = typeof window !== 'undefined' &&
                (window.location.pathname === '/login' ||
                    window.location.pathname === '/register');

            if (!isAuthPage && Cookies.get('access_token')) {
                // Token expired or invalid - redirect to login
                Cookies.remove('access_token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// Auth API
export const authApi = {
    register: async (data: RegisterData): Promise<MessageResponse> => {
        const response = await api.post<MessageResponse>('/api/auth/register', data);
        return response.data;
    },

    login: async (data: LoginData): Promise<LoginResponse> => {
        const response = await api.post<LoginResponse>('/api/auth/login', data);

        // Store token in cookie
        if (response.data.access_token) {
            Cookies.set('access_token', response.data.access_token, {
                expires: response.data.expires_in / 86400, // Convert seconds to days
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'strict',
            });
        }

        // Store auth response for redirect logic
        sessionStorage.setItem('authResponse', JSON.stringify(response.data));

        return response.data;
    },

    logout: () => {
        // === LIMPIEZA COMPLETA DE SESIÓN SEGURO ===

        // 1. Eliminar token principal
        Cookies.remove('access_token');
        Cookies.remove('admin_token');  // Si existe para admin

        // 2. Limpiar sessionStorage completamente
        if (typeof window !== 'undefined' && window.sessionStorage) {
            sessionStorage.removeItem('authResponse');
            sessionStorage.clear();  // Limpieza completa
        }

        // 3. Limpiar localStorage de datos de sesión (mantener preferencias de usuario)
        if (typeof window !== 'undefined' && window.localStorage) {
            // Preservar solo configuraciones no sensibles
            const themePreference = localStorage.getItem('theme');

            // Limpiar datos sensibles específicos
            localStorage.removeItem('admin_device_token_v1');

            // Nota: No hacer clear() para preservar preferencias del usuario
            // Solo limpiar datos de autenticación
        }

        // 4. Limpiar caché de la aplicación si es posible
        if (typeof window !== 'undefined' && 'caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    if (name.includes('auth') || name.includes('user')) {
                        caches.delete(name);
                    }
                });
            });
        }

        // 5. Redirigir al login
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
    },

    healthCheck: async (): Promise<{ status: string }> => {
        const response = await api.get('/api/auth/health');
        return response.data;
    },
};

// Face API
export const faceApi = {
    registerFace: async (data: FaceData): Promise<MessageResponse> => {
        const response = await api.post<MessageResponse>('/api/face/register', data);
        return response.data;
    },

    verifyFace: async (data: FaceData): Promise<MessageResponse> => {
        const response = await api.post<MessageResponse>('/api/face/verify', data);
        return response.data;
    },

    getStatus: async (): Promise<{
        user_id: number;
        face_registered: boolean;
        remaining_attempts?: number;
        is_locked?: boolean;
        failed_attempts?: number;
        has_backup_code?: boolean;
    }> => {
        const response = await api.get('/api/face/status');
        return response.data;
    },

    verifyBackupCode: async (code: string): Promise<MessageResponse> => {
        const response = await api.post<MessageResponse>('/api/face/backup-code/verify', { code });
        return response.data;
    },
};

export default api;
