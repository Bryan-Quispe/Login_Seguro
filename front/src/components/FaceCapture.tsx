'use client';

import React, { useState } from 'react';
import { Camera } from './Camera';
import { Button } from './ui/Button';
import { faceApi } from '@/services/api';

interface FaceCaptureProps {
    mode: 'register' | 'verify';
    onSuccess: () => void;
    onError?: (error: string) => void;
}

interface ApiResponse {
    success: boolean;
    message: string;
    data?: {
        remaining_attempts?: number;
        account_locked?: boolean;
        locked_until?: string;
        remaining_minutes?: number;
    };
}

export function FaceCapture({ mode, onSuccess, onError }: FaceCaptureProps) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error' | 'locked'>('idle');
    const [message, setMessage] = useState<string>('');
    const [remainingAttempts, setRemainingAttempts] = useState<number>(3);

    const translateError = (msg: string): string => {
        // Translate technical errors to user-friendly messages
        if (msg.includes('No se detectó') || msg.includes('no face')) {
            return 'No se detectó ningún rostro. Por favor, mire directamente a la cámara.';
        }
        if (msg.includes('spoofing') || msg.includes('Spoofing')) {
            return 'Se detectó un posible intento de suplantación. Use su rostro real.';
        }
        if (msg.includes('no coincide') || msg.includes('no match')) {
            return 'El rostro no coincide con el registrado.';
        }
        return msg;
    };

    const handleCapture = async (imageData: string) => {
        setIsProcessing(true);
        setStatus('idle');
        setMessage('');

        try {
            let response: ApiResponse;

            if (mode === 'register') {
                response = await faceApi.registerFace({ image_data: imageData });
            } else {
                response = await faceApi.verifyFace({ image_data: imageData });
            }

            if (response.success) {
                setStatus('success');
                setMessage(response.message);
                setRemainingAttempts(3); // Reset attempts
                setTimeout(() => {
                    onSuccess();
                }, 1500);
            } else {
                handleFailure(response);
            }
        } catch (err: unknown) {
            handleCatchError(err);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleFailure = (response: ApiResponse) => {
        // Check if account is locked
        if (response.data?.account_locked) {
            setStatus('locked');
            setMessage('Su cuenta ha sido bloqueada por seguridad.');
        } else {
            setStatus('error');
            const friendlyMsg = translateError(response.message || 'Error en el procesamiento facial');
            setMessage(friendlyMsg);

            if (response.data?.remaining_attempts !== undefined) {
                setRemainingAttempts(response.data.remaining_attempts);
            } else {
                // Decrement locally if not provided by server
                setRemainingAttempts(prev => Math.max(0, prev - 1));
            }
        }
        if (onError) onError(response.message);
    };

    const handleCatchError = (err: unknown) => {
        const errorResponse = (err as { response?: { data?: { detail?: string; data?: { remaining_attempts?: number; account_locked?: boolean } } } });
        const errorDetail = errorResponse?.response?.data?.detail || '';

        // Check for lockout in error response
        if (errorResponse?.response?.data?.data?.account_locked || errorDetail.includes('bloqueada')) {
            setStatus('locked');
            setMessage('Su cuenta ha sido bloqueada por seguridad.');
        } else {
            setStatus('error');
            const friendlyMsg = translateError(errorDetail || 'Error al procesar la imagen. Intente de nuevo.');
            setMessage(friendlyMsg);

            if (errorResponse?.response?.data?.data?.remaining_attempts !== undefined) {
                setRemainingAttempts(errorResponse.response.data.data.remaining_attempts);
            } else {
                setRemainingAttempts(prev => Math.max(0, prev - 1));
            }
        }
        if (onError) onError(errorDetail);
    };

    const handleCameraError = (error: string) => {
        setStatus('error');
        setMessage(translateError(error));
        if (onError) onError(error);
    };

    const handleRetry = () => {
        if (remainingAttempts > 0) {
            setStatus('idle');
            setMessage('');
        }
    };

    return (
        <div className="w-full max-w-lg mx-auto">
            {/* Header */}
            <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 mb-4">
                    <svg
                        className="w-8 h-8 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        {mode === 'register' ? (
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                            />
                        ) : (
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                            />
                        )}
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-white">
                    {mode === 'register' ? 'Registrar Rostro' : 'Verificación Facial'}
                </h2>
                <p className="mt-2 text-gray-400">
                    {mode === 'register'
                        ? 'Capture una foto clara de su rostro para completar el registro'
                        : 'Verifique su identidad con reconocimiento facial'}
                </p>
            </div>

            {/* Remaining attempts indicator */}
            {mode === 'verify' && status !== 'locked' && status !== 'success' && (
                <div className={`mb-6 p-4 rounded-lg ${remainingAttempts <= 1
                        ? 'bg-red-500/10 border border-red-500/20'
                        : remainingAttempts === 2
                            ? 'bg-yellow-500/10 border border-yellow-500/20'
                            : 'bg-blue-500/10 border border-blue-500/20'
                    }`}>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <svg
                                className={`w-5 h-5 ${remainingAttempts <= 1 ? 'text-red-400' : remainingAttempts === 2 ? 'text-yellow-400' : 'text-blue-400'}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                />
                            </svg>
                            <span className={`text-sm font-medium ${remainingAttempts <= 1 ? 'text-red-400' : remainingAttempts === 2 ? 'text-yellow-400' : 'text-blue-400'}`}>
                                Intentos restantes: {remainingAttempts}
                            </span>
                        </div>
                        <div className="flex space-x-1">
                            {[1, 2, 3].map((i) => (
                                <div
                                    key={i}
                                    className={`w-3 h-3 rounded-full ${i <= remainingAttempts
                                            ? remainingAttempts <= 1 ? 'bg-red-500' : remainingAttempts === 2 ? 'bg-yellow-500' : 'bg-blue-500'
                                            : 'bg-gray-600'
                                        }`}
                                />
                            ))}
                        </div>
                    </div>
                    {remainingAttempts <= 1 && (
                        <p className="mt-2 text-xs text-red-300">
                            ⚠️ Último intento. Si falla, su cuenta será bloqueada.
                        </p>
                    )}
                </div>
            )}

            {/* Security notice */}
            {status !== 'locked' && status !== 'error' && (
                <div className="mb-6 p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                    <div className="flex items-start space-x-3">
                        <svg
                            className="w-5 h-5 text-violet-400 mt-0.5 flex-shrink-0"
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
                        <div>
                            <p className="text-sm text-violet-300 font-medium">
                                Protección Anti-Spoofing Activa
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                                Mire directamente a la cámara. El sistema rechaza fotos y videos.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Account locked state */}
            {status === 'locked' && (
                <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-24 h-24 rounded-full bg-red-500/20 flex items-center justify-center mb-6">
                        <svg
                            className="w-12 h-12 text-red-500"
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
                    <h3 className="text-2xl font-bold text-red-400 mb-2">Cuenta Bloqueada</h3>
                    <p className="text-gray-400 text-center max-w-sm mb-6">
                        Su cuenta ha sido bloqueada temporalmente debido a múltiples intentos fallidos de verificación facial.
                    </p>
                    <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700 max-w-sm">
                        <p className="text-sm text-gray-300 text-center">
                            <span className="font-semibold text-white">¿Necesita ayuda?</span><br />
                            Contacte con el administrador del sistema para desbloquear su cuenta.
                        </p>
                        <p className="mt-3 text-xs text-gray-500 text-center">
                            📧 admin@loginseguro.com
                        </p>
                    </div>
                </div>
            )}

            {/* Camera */}
            {!isProcessing && status !== 'success' && status !== 'locked' && remainingAttempts > 0 && (
                <Camera onCapture={handleCapture} onError={handleCameraError} />
            )}

            {/* Processing state */}
            {isProcessing && (
                <div className="flex flex-col items-center justify-center py-12">
                    <div className="relative">
                        <div className="w-20 h-20 border-4 border-violet-500/30 rounded-full" />
                        <div className="absolute inset-0 w-20 h-20 border-4 border-t-violet-500 rounded-full animate-spin" />
                    </div>
                    <p className="mt-6 text-gray-300 font-medium">
                        {mode === 'register' ? 'Registrando rostro...' : 'Verificando identidad...'}
                    </p>
                    <p className="mt-2 text-sm text-gray-500">
                        Analizando con anti-spoofing
                    </p>
                </div>
            )}

            {/* Success state */}
            {status === 'success' && (
                <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center">
                        <svg
                            className="w-10 h-10 text-green-500"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M5 13l4 4L19 7"
                            />
                        </svg>
                    </div>
                    <p className="mt-6 text-green-400 font-medium">{message}</p>
                    <p className="mt-2 text-sm text-gray-500">Redirigiendo al dashboard...</p>
                </div>
            )}

            {/* Error state */}
            {status === 'error' && !isProcessing && remainingAttempts > 0 && (
                <div className="mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                    <div className="flex items-start space-x-3">
                        <svg
                            className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5"
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
                        <div className="flex-1">
                            <p className="text-sm text-red-400 font-medium">{message}</p>
                            <p className="mt-1 text-xs text-gray-400">
                                Le quedan {remainingAttempts} intento{remainingAttempts !== 1 ? 's' : ''}.
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="secondary"
                        className="w-full mt-4"
                        onClick={handleRetry}
                    >
                        Intentar de nuevo
                    </Button>
                </div>
            )}

            {/* No attempts left but not locked yet */}
            {remainingAttempts === 0 && status !== 'locked' && (
                <div className="mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-center">
                    <p className="text-red-400 font-medium">Sin intentos restantes</p>
                    <p className="mt-2 text-sm text-gray-400">
                        Por favor, contacte con el administrador.
                    </p>
                </div>
            )}
        </div>
    );
}
