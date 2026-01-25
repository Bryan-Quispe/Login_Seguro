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
        Cookies.remove('access_token');
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

    getStatus: async (): Promise<{ user_id: number; face_registered: boolean }> => {
        const response = await api.get('/api/face/status');
        return response.data;
    },
};

export default api;
