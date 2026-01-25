'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    CardFooter,
    Button,
    Input,
} from '@/components';
import { useAuth } from '@/hooks';

export default function LoginPage() {
    const router = useRouter();
    const { login, loading, error, clearError } = useAuth();

    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [formErrors, setFormErrors] = useState<Record<string, string>>({});

    const validateForm = (): boolean => {
        const errors: Record<string, string> = {};

        if (!formData.username.trim()) {
            errors.username = 'El usuario es requerido';
        }

        if (!formData.password) {
            errors.password = 'La contraseña es requerida';
        }

        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        if (!validateForm()) return;

        const success = await login(formData);

        if (success) {
            // Store temporary auth state for face pages
            sessionStorage.setItem('pendingAuth', JSON.stringify(formData));

            // Check if face registration or verification is needed
            const authData = sessionStorage.getItem('authResponse');
            if (authData) {
                const parsed = JSON.parse(authData);
                if (parsed.requires_face_registration) {
                    router.push('/face-register');
                } else if (parsed.requires_face_verification) {
                    router.push('/face-verify');
                } else {
                    // Fallback directo si no requiere verificación
                    const role = parsed.user?.role;
                    if (role === 'admin') router.push('/admin');
                    else if (role === 'auditor') router.push('/audit');
                    else router.push('/dashboard');
                }
            } else {
                // Default to face-register for first-time users
                router.push('/face-register');
            }
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
        if (formErrors[name]) {
            setFormErrors((prev) => ({ ...prev, [name]: '' }));
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 mb-4 animate-float glow-violet">
                        <svg
                            className="w-10 h-10 text-white"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                            />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold text-white">Login Seguro</h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Autenticación Biométrica Facial
                    </p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Iniciar Sesión</CardTitle>
                        <CardDescription>
                            Ingrese sus credenciales para continuar
                        </CardDescription>
                    </CardHeader>

                    <form onSubmit={handleSubmit}>
                        <CardContent>
                            <Input
                                label="Usuario"
                                name="username"
                                type="text"
                                placeholder="Ingrese su usuario"
                                value={formData.username}
                                onChange={handleChange}
                                error={formErrors.username}
                                autoComplete="username"
                                icon={
                                    <svg
                                        className="w-5 h-5"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                        />
                                    </svg>
                                }
                            />

                            <Input
                                label="Contraseña"
                                name="password"
                                type="password"
                                placeholder="Ingrese su contraseña"
                                value={formData.password}
                                onChange={handleChange}
                                error={formErrors.password}
                                autoComplete="current-password"
                                icon={
                                    <svg
                                        className="w-5 h-5"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                                        />
                                    </svg>
                                }
                            />

                            {error && (
                                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                                    <div className="flex items-center space-x-2">
                                        <svg
                                            className="w-5 h-5 text-red-400"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth={2}
                                                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                            />
                                        </svg>
                                        <span className="text-sm text-red-400">{error}</span>
                                    </div>
                                </div>
                            )}
                        </CardContent>

                        <CardFooter>
                            <Button type="submit" className="w-full" isLoading={loading}>
                                Continuar
                            </Button>

                            <p className="mt-6 text-center text-sm text-gray-400">
                                ¿No tiene una cuenta?{' '}
                                <Link
                                    href="/register"
                                    className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
                                >
                                    Regístrese aquí
                                </Link>
                            </p>
                        </CardFooter>
                    </form>
                </Card>

                {/* Security badges */}
                <div className="mt-8 flex justify-center space-x-6">
                    <div className="flex items-center space-x-2 text-gray-500 text-xs">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path
                                fillRule="evenodd"
                                d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                                clipRule="evenodd"
                            />
                        </svg>
                        <span>Cifrado SSL</span>
                    </div>
                    <div className="flex items-center space-x-2 text-gray-500 text-xs">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path
                                fillRule="evenodd"
                                d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                clipRule="evenodd"
                            />
                        </svg>
                        <span>Anti-Spoofing</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
