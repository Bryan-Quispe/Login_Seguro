'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components';
import { FaceCapture } from '@/components/FaceCapture';

export default function FaceVerifyPage() {
    const router = useRouter();

    const handleSuccess = (role?: string) => {
        // Redirigir según el rol
        if (role === 'admin') {
            router.push('/admin');
        } else if (role === 'auditor') {
            router.push('/audit');
        } else {
            router.push('/dashboard');
        }
    };

    const handleError = (error: string) => {
        console.error('Face verification error:', error);
    };

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
                                Verificación Facial
                            </span>
                        </div>
                    </div>
                </div>

                <Card>
                    <CardContent className="py-8">
                        <FaceCapture
                            mode="verify"
                            onSuccess={handleSuccess}
                            onError={handleError}
                        />
                    </CardContent>
                </Card>

                {/* Security info */}
                <div className="mt-8 p-6 rounded-xl bg-gray-900/40 backdrop-blur border border-gray-800/50">
                    <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-violet-500 to-indigo-500 flex items-center justify-center flex-shrink-0">
                            <svg
                                className="w-6 h-6 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                                />
                            </svg>
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">
                                Autenticación de Dos Factores
                            </h3>
                            <p className="mt-1 text-sm text-gray-400">
                                Su identidad está protegida por verificación biométrica facial con
                                tecnología anti-spoofing. El sistema detecta y rechaza intentos de
                                suplantación usando fotos, videos o máscaras.
                            </p>
                            <div className="mt-4 flex flex-wrap gap-2">
                                <span className="px-3 py-1 text-xs rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
                                    Anti-Spoofing
                                </span>
                                <span className="px-3 py-1 text-xs rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                    Cifrado E2E
                                </span>
                                <span className="px-3 py-1 text-xs rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">
                                    Detección de Vivacidad
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
