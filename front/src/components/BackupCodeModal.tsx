'use client';

import React, { useState } from 'react';
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from '@/components';

interface BackupCodeModalProps {
    isOpen: boolean;
    onClose: () => void;
    onVerify: (code: string) => Promise<any>;
    onSuccess: () => void;
}

export default function BackupCodeModal({
    isOpen,
    onClose,
    onVerify,
    onSuccess,
}: BackupCodeModalProps) {
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await onVerify(code);
            onSuccess();
        } catch (err: any) {
            console.error(err);
            // Manejar respuesta de error del backend
            if (err.response?.data) {
                const { message, remaining_attempts, is_locked } = err.response.data;
                let errorMsg = message || 'Código inválido';

                if (typeof remaining_attempts === 'number') {
                    errorMsg += `. Intentos restantes: ${remaining_attempts}`;
                }

                if (is_locked) {
                    errorMsg = 'Cuenta bloqueada por demasiados intentos fallidos';
                }

                setError(errorMsg);
            } else {
                setError('Código de respaldo inválido o error de conexión');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="backup-code-title"
        >
            <Card className="w-full max-w-md animate-fadeIn">
                <CardHeader>
                    <div className="flex items-center justify-center mb-4">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                            <svg
                                className="w-8 h-8 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                aria-hidden="true"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                                />
                            </svg>
                        </div>
                    </div>
                    <CardTitle className="text-center">
                        Código de Respaldo
                    </CardTitle>
                    <div id="backup-code-title" className="sr-only">Modal de código de respaldo</div>
                    <p className="text-gray-400 text-sm text-center mt-2">
                        Ingrese el código de respaldo de 8 caracteres que guardó previamente
                    </p>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input
                            label="Código de Respaldo"
                            name="backup-code"
                            type="text"
                            placeholder="Ej: A1B2C3D4"
                            value={code}
                            onChange={(e) => setCode(e.target.value.toUpperCase())}
                            maxLength={8}
                            autoComplete="off"
                            aria-label="Ingrese su código de respaldo"
                            aria-describedby={error ? 'backup-code-error' : undefined}
                            aria-invalid={!!error}
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
                            <div
                                id="backup-code-error"
                                className="p-3 rounded-lg bg-red-500/10 border border-red-500/20"
                                role="alert"
                            >
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

                        <div className="flex gap-3">
                            <Button
                                type="button"
                                variant="secondary"
                                className="flex-1"
                                onClick={onClose}
                                disabled={loading}
                            >
                                Cancelar
                            </Button>
                            <Button
                                type="submit"
                                className="flex-1"
                                isLoading={loading}
                                disabled={code.length < 8}
                                aria-busy={loading}
                            >
                                Verificar
                            </Button>
                        </div>

                        <p className="text-xs text-gray-500 text-center">
                            💡 El código de respaldo es de un solo uso
                        </p>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
