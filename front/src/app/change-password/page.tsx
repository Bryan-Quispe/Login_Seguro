'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '@/components';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export default function ChangePasswordPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [username, setUsername] = useState('');
    const [formData, setFormData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    useEffect(() => {
        const token = Cookies.get('access_token');
        if (!token) {
            router.push('/login');
            return;
        }

        // Obtener username del token
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.username) {
                setUsername(payload.username);
            }
        } catch {
            router.push('/login');
        }
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // Validaciones
        if (formData.newPassword !== formData.confirmPassword) {
            setError('Las contraseñas nuevas no coinciden');
            return;
        }

        if (formData.newPassword.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres');
            return;
        }

        if (formData.currentPassword === formData.newPassword) {
            setError('La nueva contraseña debe ser diferente a la actual');
            return;
        }

        setLoading(true);

        try {
            const token = Cookies.get('access_token');
            const response = await fetch(`${API_URL}/api/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    current_password: formData.currentPassword,
                    new_password: formData.newPassword
                })
            });

            const data = await response.json();

            if (data.success) {
                setSuccess('¡Contraseña actualizada exitosamente!');

                // Redirigir según el estado del rostro
                setTimeout(() => {
                    if (data.requires_face_registration) {
                        router.push('/face-register');
                    } else {
                        router.push('/face-verify');
                    }
                }, 1500);
            } else {
                setError(data.detail || data.message || 'Error al cambiar contraseña');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
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
                    <CardTitle className="text-2xl">Cambiar Contraseña</CardTitle>
                    <p className="text-gray-400 mt-2">
                        Hola <span className="text-white font-semibold">{username}</span>,
                        es necesario cambiar tu contraseña temporal.
                    </p>
                </CardHeader>

                <CardContent>
                    <div className="mb-6 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                        <p className="text-sm text-amber-400">
                            ⚠️ <strong>Primer acceso:</strong> Tu contraseña temporal es igual a tu nombre de usuario.
                            Debes cambiarla antes de continuar.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input
                            label="Contraseña Actual (tu nombre de usuario)"
                            name="currentPassword"
                            type="password"
                            value={formData.currentPassword}
                            onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                            placeholder="Ingresa tu contraseña actual"
                            required
                            aria-required="true"
                        />

                        <Input
                            label="Nueva Contraseña"
                            name="newPassword"
                            type="password"
                            value={formData.newPassword}
                            onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                            placeholder="Mínimo 8 caracteres"
                            required
                            aria-required="true"
                        />

                        <Input
                            label="Confirmar Nueva Contraseña"
                            name="confirmPassword"
                            type="password"
                            value={formData.confirmPassword}
                            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                            placeholder="Repite la nueva contraseña"
                            required
                            aria-required="true"
                        />

                        {error && (
                            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {success && (
                            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm">
                                {success}
                            </div>
                        )}

                        <Button
                            type="submit"
                            className="w-full"
                            isLoading={loading}
                            aria-label="Cambiar contraseña"
                        >
                            Cambiar Contraseña y Continuar
                        </Button>
                    </form>

                    <div className="mt-6 text-center text-sm text-gray-500">
                        Después de cambiar tu contraseña, continuarás con el registro facial.
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
