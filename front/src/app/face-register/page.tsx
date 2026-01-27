'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { Card, CardContent } from '@/components';
import { FaceCapture } from '@/components/FaceCapture';

export default function FaceRegisterPage() {
    const router = useRouter();
    const [isAuthorized, setIsAuthorized] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Verificar autenticación al cargar
    useEffect(() => {
        const token = Cookies.get('access_token');
        if (!token) {
            router.push('/login');
            return;
        }
        setIsAuthorized(true);
        setIsLoading(false);
    }, [router]);

    const handleSuccess = (role?: string) => {
        // Face registered successfully, redirect based on role
        if (role === 'admin') {
            router.push('/admin');
        } else if (role === 'auditor') {
            router.push('/audit');
        } else {
            // Si no viene el rol en la respuesta, intentar obtenerlo del token
            const token = Cookies.get('access_token');
            if (token) {
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    if (payload.role === 'admin') {
                        router.push('/admin');
                        return;
                    } else if (payload.role === 'auditor') {
                        router.push('/audit');
                        return;
                    }
                } catch { /* ignore parse errors */ }
            }
            router.push('/dashboard');
        }
    };

    const handleError = (error: string) => {
        console.error('Face registration error:', error);
    };

    // Mostrar loading mientras verifica autenticación
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500"></div>
            </div>
        );
    }

    // Si no está autorizado, no mostrar nada (se redirige)
    if (!isAuthorized) {
        return null;
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-2xl">
                {/* Progress indicator */}
                <div className="mb-8">
                    <div className="flex items-center justify-center space-x-4">
                        <div className="flex items-center">
                            <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white text-sm font-bold">
                                ✓
                            </div>
                            <span className="ml-2 text-sm text-gray-400">Credenciales</span>
                        </div>
                        <div className="w-16 h-0.5 bg-gradient-to-r from-green-500 to-violet-500" />
                        <div className="flex items-center">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold animate-pulse">
                                2
                            </div>
                            <span className="ml-2 text-sm text-white font-medium">
                                Registro Facial
                            </span>
                        </div>
                    </div>
                </div>

                <Card>
                    <CardContent className="py-8">
                        <FaceCapture
                            mode="register"
                            onSuccess={handleSuccess}
                            onError={handleError}
                        />
                    </CardContent>
                </Card>

                {/* Info section */}
                <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg bg-gray-900/40 backdrop-blur border border-gray-800/50">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                                <svg
                                    className="w-5 h-5 text-violet-400"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                                    />
                                </svg>
                            </div>
                            <div>
                                <p className="text-sm font-medium text-white">Buena iluminación</p>
                                <p className="text-xs text-gray-500">Frente a una fuente de luz</p>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 rounded-lg bg-gray-900/40 backdrop-blur border border-gray-800/50">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                                <svg
                                    className="w-5 h-5 text-violet-400"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                    />
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                    />
                                </svg>
                            </div>
                            <div>
                                <p className="text-sm font-medium text-white">Rostro visible</p>
                                <p className="text-xs text-gray-500">Sin lentes ni accesorios</p>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 rounded-lg bg-gray-900/40 backdrop-blur border border-gray-800/50">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center">
                                <svg
                                    className="w-5 h-5 text-violet-400"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                                    />
                                </svg>
                            </div>
                            <div>
                                <p className="text-sm font-medium text-white">Expresión neutral</p>
                                <p className="text-xs text-gray-500">Mire directamente a la cámara</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
