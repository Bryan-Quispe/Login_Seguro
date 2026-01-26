'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { Card, CardContent, CardHeader, CardTitle, Button } from '@/components';
import { authApi } from '@/services/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

interface UserProfile {
    id: number;
    username: string;
    email: string | null;
    role: string;
    face_registered: boolean;
    has_backup_code: boolean;
    created_at: string | null;
    updated_at: string | null;
}

export default function DashboardPage() {
    const router = useRouter();
    const [username, setUsername] = useState<string>('Usuario');
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [showProfile, setShowProfile] = useState(false);
    const [backupCode, setBackupCode] = useState<string | null>(null);
    const [generatingCode, setGeneratingCode] = useState(false);
    const [message, setMessage] = useState('');

    const fetchProfile = useCallback(async (token: string) => {
        try {
            const response = await fetch(`${API_URL}/api/auth/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (data.success && data.user) {
                setProfile(data.user);
            }
        } catch (error) {
            console.error('Error fetching profile:', error);
        }
    }, []);

    useEffect(() => {
        // Check if user is authenticated
        const token = Cookies.get('access_token');
        if (!token) {
            router.push('/login');
            return;
        }

        // Try to get username from token
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.username) {
                setUsername(payload.username);
            }
        } catch (e) {
            console.error('Error parsing token:', e);
        }

        // Fetch profile
        fetchProfile(token);
    }, [router, fetchProfile]);

    const handleLogout = () => {
        authApi.logout();
    };

    const handleGenerateBackupCode = async () => {
        const token = Cookies.get('access_token');
        if (!token) return;

        setGeneratingCode(true);
        setMessage('');

        try {
            const response = await fetch(`${API_URL}/api/face/backup-code/generate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();

            if (data.success && data.backup_code) {
                setBackupCode(data.backup_code);
                setMessage('¡Código generado! Guárdelo en un lugar seguro.');
                // Actualizar profile
                fetchProfile(token);
            } else {
                setMessage(data.message || 'Error al generar código');
            }
        } catch {
            setMessage('Error de conexión');
        } finally {
            setGeneratingCode(false);
        }
    };

    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'No disponible';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen p-4 md:p-8">
            {/* Header */}
            <header className="max-w-6xl mx-auto mb-8">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center">
                            <svg
                                className="w-6 h-6 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                aria-hidden="true"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                                />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Login Seguro</h1>
                            <p className="text-sm text-gray-400">Panel de Control</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <Button
                            variant="secondary"
                            onClick={() => setShowProfile(!showProfile)}
                            aria-label="Ver mi perfil"
                        >
                            👤 Mi Perfil
                        </Button>
                        <Button variant="ghost" onClick={handleLogout} aria-label="Cerrar sesión">
                            <svg
                                className="w-5 h-5 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                                />
                            </svg>
                            Cerrar Sesión
                        </Button>
                    </div>
                </div>
            </header>

            {/* Main content */}
            <main className="max-w-6xl mx-auto">
                {/* Profile Section - Expandible */}
                {showProfile && profile && (
                    <Card className="mb-8 border-violet-500/30">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <span className="text-2xl">👤</span>
                                Mi Perfil
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Información básica */}
                                <div className="space-y-4">
                                    <h4 className="text-lg font-semibold text-white mb-4">Información de la Cuenta</h4>
                                    <div className="space-y-3">
                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                            <span className="text-gray-400">Usuario</span>
                                            <span className="text-white font-medium">{profile.username}</span>
                                        </div>
                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                            <span className="text-gray-400">Correo</span>
                                            <span className="text-white">{profile.email || 'No configurado'}</span>
                                        </div>
                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                            <span className="text-gray-400">Rol</span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${profile.role === 'admin' ? 'bg-red-500/20 text-red-400' :
                                                    profile.role === 'auditor' ? 'bg-purple-500/20 text-purple-400' :
                                                        'bg-blue-500/20 text-blue-400'
                                                }`}>
                                                {profile.role}
                                            </span>
                                        </div>
                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                            <span className="text-gray-400">Registro facial</span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${profile.face_registered
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : 'bg-yellow-500/20 text-yellow-400'
                                                }`}>
                                                {profile.face_registered ? '✓ Configurado' : 'Pendiente'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between py-2">
                                            <span className="text-gray-400">Fecha de registro</span>
                                            <span className="text-white text-sm">{formatDate(profile.created_at)}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Código de respaldo */}
                                <div className="space-y-4">
                                    <h4 className="text-lg font-semibold text-white mb-4">Código de Respaldo</h4>
                                    <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
                                        <p className="text-sm text-gray-400 mb-4">
                                            El código de respaldo permite acceder cuando falla la verificación facial.
                                            Es de un solo uso.
                                        </p>

                                        <div className="flex items-center gap-2 mb-4">
                                            <span className="text-gray-400">Estado:</span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${profile.has_backup_code
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : 'bg-yellow-500/20 text-yellow-400'
                                                }`}>
                                                {profile.has_backup_code ? '✓ Configurado' : 'No configurado'}
                                            </span>
                                        </div>

                                        {backupCode && (
                                            <div className="p-4 mb-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                                                <p className="text-sm text-amber-400 mb-2">
                                                    ⚠️ Guarde este código, solo se muestra una vez:
                                                </p>
                                                <p className="text-2xl font-mono font-bold text-white tracking-widest text-center">
                                                    {backupCode}
                                                </p>
                                            </div>
                                        )}

                                        {message && (
                                            <p className={`text-sm mb-4 ${backupCode ? 'text-green-400' : 'text-red-400'}`}>
                                                {message}
                                            </p>
                                        )}

                                        <Button
                                            onClick={handleGenerateBackupCode}
                                            isLoading={generatingCode}
                                            className="w-full"
                                            aria-label="Generar código de respaldo"
                                        >
                                            {profile.has_backup_code ? '🔄 Regenerar Código' : '🔐 Generar Código'}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Welcome card */}
                <Card className="mb-8">
                    <CardContent className="py-8">
                        <div className="flex flex-col md:flex-row items-center justify-between">
                            <div className="flex items-center space-x-6 mb-6 md:mb-0">
                                <div className="relative">
                                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                                        <span className="text-3xl font-bold text-white">
                                            {username.charAt(0).toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-green-500 border-2 border-gray-900 flex items-center justify-center">
                                        <svg
                                            className="w-3 h-3 text-white"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            aria-hidden="true"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                    </div>
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-white">
                                        ¡Bienvenido, {username}!
                                    </h2>
                                    <p className="text-gray-400">
                                        Tu identidad ha sido verificada exitosamente
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center space-x-3">
                                <div className="px-4 py-2 rounded-lg bg-green-500/10 border border-green-500/20">
                                    <div className="flex items-center space-x-2">
                                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                        <span className="text-sm text-green-400 font-medium">
                                            Sesión Activa
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Stats grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <Card>
                        <CardContent className="py-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-400">Estado de Seguridad</p>
                                    <p className="text-2xl font-bold text-green-400 mt-1">Óptimo</p>
                                </div>
                                <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                                    <svg
                                        className="w-6 h-6 text-green-400"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        aria-hidden="true"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                                        />
                                    </svg>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="py-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-400">Autenticación</p>
                                    <p className="text-2xl font-bold text-violet-400 mt-1">Biométrica</p>
                                </div>
                                <div className="w-12 h-12 rounded-lg bg-violet-500/20 flex items-center justify-center">
                                    <svg
                                        className="w-6 h-6 text-violet-400"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        aria-hidden="true"
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
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="py-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-400">Anti-Spoofing</p>
                                    <p className="text-2xl font-bold text-blue-400 mt-1">Activo</p>
                                </div>
                                <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                    <svg
                                        className="w-6 h-6 text-blue-400"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        aria-hidden="true"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                                        />
                                    </svg>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Security features */}
                <Card>
                    <CardContent className="py-8">
                        <h3 className="text-lg font-semibold text-white mb-6">
                            Características de Seguridad Activas
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {[
                                {
                                    title: 'Protección SQL Injection',
                                    desc: 'Consultas parametrizadas en todas las operaciones',
                                    icon: '🛡️',
                                },
                                {
                                    title: 'Hash Bcrypt',
                                    desc: 'Contraseñas cifradas con 12 rondas de salt',
                                    icon: '🔐',
                                },
                                {
                                    title: 'Anti-Spoofing Facial',
                                    desc: 'Detección de fotos, videos y máscaras 3D',
                                    icon: '👤',
                                },
                                {
                                    title: 'Rate Limiting',
                                    desc: 'Protección contra ataques de fuerza bruta',
                                    icon: '⚡',
                                },
                                {
                                    title: 'JWT Seguro',
                                    desc: 'Tokens firmados con expiración automática',
                                    icon: '🎟️',
                                },
                                {
                                    title: 'Código de Respaldo',
                                    desc: 'Fallback seguro para autenticación biométrica',
                                    icon: '🔑',
                                },
                            ].map((feature, index) => (
                                <div
                                    key={index}
                                    className="flex items-start space-x-4 p-4 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
                                >
                                    <span className="text-2xl" aria-hidden="true">{feature.icon}</span>
                                    <div>
                                        <p className="font-medium text-white">{feature.title}</p>
                                        <p className="text-sm text-gray-400">{feature.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}

