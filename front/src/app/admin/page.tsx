'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '@/components';
import Cookies from 'js-cookie';

// Token secreto del dispositivo - Solo tu computadora tendrá este token
// IMPORTANTE: Este token se genera una sola vez y se guarda en localStorage
const DEVICE_SECRET_KEY = 'admin_device_token_v1';
const MASTER_DEVICE_TOKEN = 'BQUISPE-LAPTOP-2024-ADMIN-TOKEN-SECURE'; // Token que debes tener

interface User {
    id: number;
    username: string;
    email: string;
    role: string;
    face_registered: boolean;
    is_locked: boolean;
    locked_until: string | null;
    failed_attempts: number;
    requires_password_reset: boolean;
}

interface Stats {
    total_users: number;
    blocked_users: number;
    users_with_face_registered: number;
    users_pending_password_reset: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export default function AdminPage() {
    const [deviceAuthorized, setDeviceAuthorized] = useState<boolean | null>(null);
    const [showDeviceSetup, setShowDeviceSetup] = useState(false);
    const [deviceTokenInput, setDeviceTokenInput] = useState('');
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loginData, setLoginData] = useState({ username: '', password: '' });
    const [users, setUsers] = useState<User[]>([]);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(false);
    const [processingUserId, setProcessingUserId] = useState<number | null>(null);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Verificar token de dispositivo al cargar
    const router = useRouter();

    useEffect(() => {
        checkDeviceAuthorization();
    }, []);

    const checkDeviceAuthorization = () => {
        const storedToken = localStorage.getItem(DEVICE_SECRET_KEY);

        if (storedToken === MASTER_DEVICE_TOKEN) {
            setDeviceAuthorized(true);
            // Verificar si ya tiene sesión (access_token del login principal)
            const token = Cookies.get('access_token');
            if (token) {
                setIsAuthenticated(true);
                fetchData(token);
            } else {
                // No hay sesión, redirigir a login
                router.push('/login');
            }
        } else if (!storedToken) {
            // Primer acceso - mostrar setup
            setShowDeviceSetup(true);
            setDeviceAuthorized(false);
        } else {
            // Token incorrecto
            setDeviceAuthorized(false);
        }
    };

    const handleDeviceSetup = (e: React.FormEvent) => {
        e.preventDefault();
        if (deviceTokenInput === MASTER_DEVICE_TOKEN) {
            localStorage.setItem(DEVICE_SECRET_KEY, deviceTokenInput);
            setDeviceAuthorized(true);
            setShowDeviceSetup(false);
        } else {
            setError('Token de dispositivo inválido');
        }
    };

    // Validar y cargar datos
    const fetchData = async (token: string) => {
        try {
            // Primero validar que sea admin verificando stats
            const statsRes = await fetch(`${API_URL}/api/admin/stats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!statsRes.ok) {
                setError('Acceso denegado. Se requiere rol de administrador.');
                setIsAuthenticated(false);
                return;
            }

            const statsData = await statsRes.json();
            if (statsData.success) {
                setStats(statsData.stats);
            }

            const usersRes = await fetch(`${API_URL}/api/admin/users`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const usersData = await usersRes.json();
            if (usersData.success) {
                setUsers(usersData.users);
            }

        } catch (err) {
            console.error('Error fetching data:', err);
            setError('Error de conexión o sesión inválida');
        }
    };

    const handleUnlock = async (userId: number, username: string) => {
        const token = Cookies.get('access_token') || Cookies.get('admin_token');
        if (!token) return;

        setProcessingUserId(userId);
        setError('');
        setSuccess('');

        try {
            const response = await fetch(`${API_URL}/api/admin/unlock/${userId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (data.success) {
                setSuccess(`Usuario "${username}" desbloqueado. Debe registrar nueva contraseña y rostro.`);
                fetchData(token);
            } else {
                setError(data.message || 'Error al desbloquear');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setProcessingUserId(null);
        }
    };

    const handleDisable = async (userId: number, username: string) => {
        const token = Cookies.get('access_token') || Cookies.get('admin_token');
        if (!token) return;

        if (!confirm(`¿Está seguro de deshabilitar al usuario "${username}"?`)) return;

        setProcessingUserId(userId);
        setError('');
        setSuccess('');

        try {
            const response = await fetch(`${API_URL}/api/admin/disable/${userId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (data.success) {
                setSuccess(`Usuario "${username}" deshabilitado.`);
                fetchData(token);
            } else {
                setError(data.message || data.detail || 'Error al deshabilitar');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setProcessingUserId(null);
        }
    };

    const handleEnable = async (userId: number, username: string) => {
        const token = Cookies.get('access_token') || Cookies.get('admin_token');
        if (!token) return;

        setProcessingUserId(userId);
        setError('');
        setSuccess('');

        try {
            const response = await fetch(`${API_URL}/api/admin/enable/${userId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (data.success) {
                setSuccess(`Usuario "${username}" habilitado.`);
                fetchData(token);
            } else {
                setError(data.message || data.detail || 'Error al habilitar');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setProcessingUserId(null);
        }
    };

    const handleLogout = () => {
        Cookies.remove('admin_token');
        Cookies.remove('access_token');
        setIsAuthenticated(false);
        setUsers([]);
        setStats(null);
        router.push('/login');
    };

    // Pantalla de acceso denegado - dispositivo no autorizado
    if (deviceAuthorized === false && !showDeviceSetup) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardContent className="py-12 text-center">
                        <div className="w-20 h-20 mx-auto rounded-full bg-red-500/20 flex items-center justify-center mb-6">
                            <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-red-400 mb-2">Acceso Denegado</h2>
                        <p className="text-gray-400 mb-6">
                            Este dispositivo no está autorizado para acceder al panel de administración.
                        </p>
                        <p className="text-sm text-gray-500">
                            Solo dispositivos autorizados pueden acceder.
                        </p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Pantalla de configuración inicial de dispositivo
    if (showDeviceSetup) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 mb-4">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                            <CardTitle>Autorizar Dispositivo</CardTitle>
                            <p className="text-gray-400 text-sm mt-2">
                                Primer acceso detectado. Ingrese el token de dispositivo para autorizar esta computadora.
                            </p>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleDeviceSetup} className="space-y-4">
                            <Input
                                label="Token de Dispositivo"
                                type="password"
                                value={deviceTokenInput}
                                onChange={(e) => setDeviceTokenInput(e.target.value)}
                                placeholder="Ingrese el token secreto..."
                            />
                            {error && (
                                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                                    {error}
                                </div>
                            )}
                            <Button type="submit" className="w-full">
                                Autorizar Este Dispositivo
                            </Button>
                            <p className="text-xs text-gray-500 text-center">
                                ⚠️ Solo autoriza tu dispositivo personal
                            </p>
                        </form>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Pantalla de autorización verificando
    if (!isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 mb-4 animate-pulse">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <CardTitle>Verificando Acceso...</CardTitle>
                            <p className="text-gray-400 text-sm mt-2">Validando credenciales de administrador</p>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {error && (
                            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                                {error}
                                <Button
                                    className="mt-2 w-full"
                                    variant="secondary"
                                    onClick={() => router.push('/login')}
                                >
                                    Ir al Login
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Panel de admin
    return (
        <div className="min-h-screen p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Panel de Administrador</h1>
                        <p className="text-gray-400 mt-1">Gestión de usuarios del sistema</p>
                    </div>
                    <Button variant="secondary" onClick={handleLogout}>
                        Cerrar Sesión
                    </Button>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                            <p className="text-3xl font-bold text-white">{stats.total_users}</p>
                            <p className="text-gray-400 text-sm">Usuarios totales</p>
                        </div>
                        <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
                            <p className="text-3xl font-bold text-red-400">{stats.blocked_users}</p>
                            <p className="text-gray-400 text-sm">Bloqueados</p>
                        </div>
                        <div className="bg-green-500/10 rounded-xl p-4 border border-green-500/30">
                            <p className="text-3xl font-bold text-green-400">{stats.users_with_face_registered}</p>
                            <p className="text-gray-400 text-sm">Con rostro registrado</p>
                        </div>
                        <div className="bg-yellow-500/10 rounded-xl p-4 border border-yellow-500/30">
                            <p className="text-3xl font-bold text-yellow-400">{stats.users_pending_password_reset}</p>
                            <p className="text-gray-400 text-sm">Pendientes reset</p>
                        </div>
                    </div>
                )}

                {/* Messages */}
                {success && (
                    <div className="mb-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400">
                        ✓ {success}
                    </div>
                )}
                {error && (
                    <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
                        ✗ {error}
                    </div>
                )}

                {/* Users Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Lista de Usuarios</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-700">
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Usuario</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Email</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Rostro</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Estado</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Intentos</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map((user) => (
                                        <tr key={user.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                                            <td className="py-3 px-4 text-white font-medium">{user.username}</td>
                                            <td className="py-3 px-4 text-gray-300">{user.email || '-'}</td>
                                            <td className="py-3 px-4">
                                                {user.face_registered ? (
                                                    <span className="px-2 py-1 text-xs bg-green-500/10 text-green-400 rounded-full">
                                                        ✓ Registrado
                                                    </span>
                                                ) : (
                                                    <span className="px-2 py-1 text-xs bg-gray-500/10 text-gray-400 rounded-full">
                                                        Pendiente
                                                    </span>
                                                )}
                                            </td>
                                            <td className="py-3 px-4">
                                                {user.is_locked ? (
                                                    <span className="px-2 py-1 text-xs bg-red-500/10 text-red-400 rounded-full">
                                                        🔒 Bloqueado
                                                    </span>
                                                ) : user.requires_password_reset ? (
                                                    <span className="px-2 py-1 text-xs bg-yellow-500/10 text-yellow-400 rounded-full">
                                                        ⚠️ Resetear pass
                                                    </span>
                                                ) : (
                                                    <span className="px-2 py-1 text-xs bg-green-500/10 text-green-400 rounded-full">
                                                        ✓ Activo
                                                    </span>
                                                )}
                                            </td>
                                            <td className="py-3 px-4 text-gray-300">{user.failed_attempts}</td>
                                            <td className="py-3 px-4">
                                                <div className="flex gap-2">
                                                    {user.is_locked ? (
                                                        <>
                                                            <Button
                                                                variant="primary"
                                                                className="text-xs py-1 px-3"
                                                                onClick={() => handleUnlock(user.id, user.username)}
                                                                isLoading={processingUserId === user.id}
                                                            >
                                                                🔓 Desbloquear
                                                            </Button>
                                                            <Button
                                                                variant="secondary"
                                                                className="text-xs py-1 px-3 bg-green-500/20 hover:bg-green-500/30 text-green-400"
                                                                onClick={() => handleEnable(user.id, user.username)}
                                                                isLoading={processingUserId === user.id}
                                                            >
                                                                ✓ Habilitar
                                                            </Button>
                                                        </>
                                                    ) : (
                                                        <Button
                                                            variant="secondary"
                                                            className="text-xs py-1 px-3 bg-red-500/20 hover:bg-red-500/30 text-red-400"
                                                            onClick={() => handleDisable(user.id, user.username)}
                                                            isLoading={processingUserId === user.id}
                                                        >
                                                            ✗ Deshabilitar
                                                        </Button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {users.length === 0 && (
                                        <tr>
                                            <td colSpan={6} className="py-8 text-center text-gray-400">
                                                No hay usuarios registrados
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>

                {/* Info Box */}
                <div className="mt-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700">
                    <h3 className="text-lg font-semibold text-white mb-3">ℹ️ Información del Sistema</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                            <p className="text-gray-400 mb-1">Librería de Reconocimiento:</p>
                            <p className="text-white">OpenCV con Haar Cascades</p>
                        </div>
                        <div>
                            <p className="text-gray-400 mb-1">Almacenamiento facial:</p>
                            <p className="text-white">JSON (128 valores) en PostgreSQL</p>
                        </div>
                        <div>
                            <p className="text-gray-400 mb-1">Intentos permitidos:</p>
                            <p className="text-white">3 intentos de verificación facial</p>
                        </div>
                        <div>
                            <p className="text-gray-400 mb-1">Seguridad del panel:</p>
                            <p className="text-white">Token de dispositivo + JWT</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
