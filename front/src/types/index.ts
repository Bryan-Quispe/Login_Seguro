// Types for the Login Seguro application

export interface User {
    id: number;
    username: string;
    email?: string;
    face_registered: boolean;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    user: User;
    requires_face_registration: boolean;
    requires_face_verification: boolean;
}

export interface MessageResponse {
    success: boolean;
    message: string;
    data?: Record<string, unknown>;
}

export interface RegisterData {
    username: string;
    password: string;
    email?: string;
}

export interface LoginData {
    username: string;
    password: string;
}

export interface FaceData {
    image_data: string;
}

export interface AuthState {
    isAuthenticated: boolean;
    user: User | null;
    token: string | null;
    requiresFaceRegistration: boolean;
    requiresFaceVerification: boolean;
    faceVerified: boolean;
}
