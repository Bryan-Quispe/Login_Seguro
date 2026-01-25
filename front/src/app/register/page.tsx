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

export default function RegisterPage() {
    const router = useRouter();
    const { register, loading, error, clearError } = useAuth();

    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
    });
    const [formErrors, setFormErrors] = useState<Record<string, string>>({});
    const [success, setSuccess] = useState(false);

    const validateForm = (): boolean => {
        const errors: Record<string, string> = {};

        // Username validation
        if (!formData.username.trim()) {
            errors.username = 'El usuario es requerido';
        } else if (formData.username.length < 3) {
            errors.username = 'El usuario debe tener al menos 3 caracteres';
        } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
            errors.username = 'Solo letras, números y guiones bajos';
        }

        // Email validation (optional)
        if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            errors.email = 'Email inválido';
        }

        // Password validation
        if (!formData.password) {
            errors.password = 'La contraseña es requerida';
        } else {
            if (formData.password.length < 8) {
                errors.password = 'Mínimo 8 caracteres';
            } else if (!/[A-Z]/.test(formData.password)) {
                errors.password = 'Debe contener una mayúscula';
            } else if (!/[a-z]/.test(formData.password)) {
                errors.password = 'Debe contener una minúscula';
            } else if (!/\d/.test(formData.password)) {
                errors.password = 'Debe contener un número';
            } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(formData.password)) {
                errors.password = 'Debe contener un carácter especial';
            }
        }

        // Confirm password
        if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = 'Las contraseñas no coinciden';
        }

        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        if (!validateForm()) return;

        const success = await register({
            username: formData.username,
            password: formData.password,
            email: formData.email || undefined,
        });

        if (success) {
            setSuccess(true);
            setTimeout(() => {
                router.push('/login');
            }, 2000);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
        if (formErrors[name]) {
            setFormErrors((prev) => ({ ...prev, [name]: '' }));
        }
    };

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4">
                <Card className="w-full max-w-md text-center">
                    <CardContent>
                        <div className="flex flex-col items-center py-8">
                            <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mb-6">
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
                            <h2 className="text-2xl font-bold text-white mb-2">
                                ¡Registro Exitoso!
                            </h2>
                            <p className="text-gray-400">
                                Redirigiendo al inicio de sesión...
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

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
                                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                            />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold text-white">Crear Cuenta</h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Únase al sistema de autenticación segura
                    </p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Registro</CardTitle>
                        <CardDescription>
                            Complete el formulario para crear su cuenta
                        </CardDescription>
                    </CardHeader>

                    <form onSubmit={handleSubmit}>
                        <CardContent>
                            <Input
                                label="Usuario"
                                name="username"
                                type="text"
                                placeholder="Ej: juan_perez"
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
                                label="Email (opcional)"
                                name="email"
                                type="email"
                                placeholder="ejemplo@correo.com"
                                value={formData.email}
                                onChange={handleChange}
                                error={formErrors.email}
                                autoComplete="email"
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
                                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                        />
                                    </svg>
                                }
                            />

                            <Input
                                label="Contraseña"
                                name="password"
                                type="password"
                                placeholder="Mínimo 8 caracteres"
                                value={formData.password}
                                onChange={handleChange}
                                error={formErrors.password}
                                autoComplete="new-password"
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

                            <Input
                                label="Confirmar Contraseña"
                                name="confirmPassword"
                                type="password"
                                placeholder="Repita su contraseña"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                error={formErrors.confirmPassword}
                                autoComplete="new-password"
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
                                            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                                        />
                                    </svg>
                                }
                            />

                            {/* Password requirements */}
                            <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
                                <p className="text-xs text-gray-400 font-medium mb-2">
                                    La contraseña debe contener:
                                </p>
                                <ul className="text-xs text-gray-500 space-y-1">
                                    <li className={formData.password.length >= 8 ? 'text-green-400' : ''}>
                                        ✓ Mínimo 8 caracteres
                                    </li>
                                    <li className={/[A-Z]/.test(formData.password) ? 'text-green-400' : ''}>
                                        ✓ Una letra mayúscula
                                    </li>
                                    <li className={/[a-z]/.test(formData.password) ? 'text-green-400' : ''}>
                                        ✓ Una letra minúscula
                                    </li>
                                    <li className={/\d/.test(formData.password) ? 'text-green-400' : ''}>
                                        ✓ Un número
                                    </li>
                                    <li className={/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'text-green-400' : ''}>
                                        ✓ Un carácter especial (!@#$%...)
                                    </li>
                                </ul>
                            </div>

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
                                Crear Cuenta
                            </Button>

                            <p className="mt-6 text-center text-sm text-gray-400">
                                ¿Ya tiene una cuenta?{' '}
                                <Link
                                    href="/login"
                                    className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
                                >
                                    Inicie sesión
                                </Link>
                            </p>
                        </CardFooter>
                    </form>
                </Card>
            </div>
        </div>
    );
}
