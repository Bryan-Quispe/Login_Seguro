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
    users_pending_face_registration: number;
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
    const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(false);
    const [processingUserId, setProcessingUserId] = useState<number | null>(null);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const USERS_PER_PAGE = 10;
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [adminName, setAdminName] = useState('Administrador');
    const [newUserData, setNewUserData] = useState({
        username: '',
        email: '',
        role: 'user'
    });

    // Estado para código de respaldo del admin
    const [backupCode, setBackupCode] = useState<string | null>(null);
    const [generatingCode, setGeneratingCode] = useState(false);
    const [hasExistingBackupCode, setHasExistingBackupCode] = useState<boolean>(false);

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
                fetchBackupCodeStatus(token);
                // Obtener nombre del admin del token
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    if (payload.username) setAdminName(payload.username);
                } catch { /* ignore parse errors */ }
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

            // Verificar si ya tiene sesión activa
            const token = Cookies.get('access_token');
            if (token) {
                // Ya tiene sesión, cargar datos del admin
                setIsAuthenticated(true);
                fetchData(token);
                fetchBackupCodeStatus(token);
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    if (payload.username) setAdminName(payload.username);
                } catch { /* ignore */ }
            } else {
                // No hay sesión, redirigir a login inmediatamente
                router.push('/login');
            }
        } else {
            setError('Token de dispositivo inválido');
        }
    };

    // Obtener estado del código de respaldo
    const fetchBackupCodeStatus = async (token: string) => {
        try {
            const response = await fetch(`${API_URL}/api/face/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (data.has_backup_code !== undefined) {
                setHasExistingBackupCode(data.has_backup_code);
            }
        } catch (error) {
            console.error('Error fetching backup code status:', error);
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
                setFilteredUsers(usersData.users);
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

    // Generar código de respaldo para el admin
    const handleGenerateBackupCode = async () => {
        const token = Cookies.get('access_token');
        if (!token) return;

        setGeneratingCode(true);
        setSuccess('');
        setError('');

        try {
            const response = await fetch(`${API_URL}/api/face/backup-code/generate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();

            if (data.success && data.backup_code) {
                setBackupCode(data.backup_code);
                setHasExistingBackupCode(true);
                setSuccess('¡Código de respaldo generado! Guárdelo en un lugar seguro.');
            } else {
                setError(data.message || 'Error al generar código');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setGeneratingCode(false);
        }
    };

    // ===== NUEVAS FUNCIONES PARA GESTIÓN DE USUARIOS =====

    // Búsqueda de usuarios
    const handleSearch = (query: string) => {
        setSearchQuery(query);
        setCurrentPage(1); // Reset to first page on search
        if (!query.trim()) {
            setFilteredUsers(users);
        } else {
            const filtered = users.filter(
                u => u.username.toLowerCase().includes(query.toLowerCase()) ||
                    (u.email && u.email.toLowerCase().includes(query.toLowerCase()))
            );
            setFilteredUsers(filtered);
        }
    };

    // Pagination logic
    const totalPages = Math.ceil(filteredUsers.length / USERS_PER_PAGE);
    const paginatedUsers = filteredUsers.slice(
        (currentPage - 1) * USERS_PER_PAGE,
        currentPage * USERS_PER_PAGE
    );

    // Crear usuario
    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        const token = Cookies.get('access_token');
        if (!token) return;

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_URL}/api/admin/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newUserData)
            });

            const data = await response.json();

            if (data.success) {
                setSuccess(`Usuario "${newUserData.username}" creado exitosamente.`);
                setShowCreateModal(false);
                setNewUserData({ username: '', email: '', role: 'user' });
                fetchData(token);
            } else {
                setError(data.detail || data.message || 'Error al crear usuario');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setLoading(false);
        }
    };

    // Editar usuario
    const handleEditUser = async (e: React.FormEvent) => {
        e.preventDefault();
        const token = Cookies.get('access_token');
        if (!token || !editingUser) return;

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_URL}/api/admin/users/${editingUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    email: editingUser.email,
                    role: editingUser.role,
                    requires_password_reset: editingUser.requires_password_reset
                })
            });

            const data = await response.json();

            if (data.success) {
                setSuccess(`Usuario "${editingUser.username}" actualizado.`);
                setShowEditModal(false);
                setEditingUser(null);
                fetchData(token);
            } else {
                setError(data.detail || data.message || 'Error al actualizar usuario');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setLoading(false);
        }
    };

    const openEditModal = (user: User) => {
        setEditingUser({ ...user });
        setShowEditModal(true);
    };

    // Obtener hora del día para saludo
    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return '¡Buenos días';
        if (hour < 18) return '¡Buenas tardes';
        return '¡Buenas noches';
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
                        {!error && (
                            <div className="text-center text-gray-400 text-sm">
                                <p>Redirigiendo al login...</p>
                                <Button
                                    className="mt-4 w-full"
                                    variant="secondary"
                                    onClick={() => router.push('/login')}
                                >
                                    Ir al Login Ahora
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
                {/* Header con bienvenida personalizada */}
                <div className="mb-8">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-white">
                                {getGreeting()}, {adminName}!
                            </h1>
                            <p className="text-gray-400 mt-1">Panel de Administración - Gestión de usuarios del sistema</p>
                        </div>
                        <Button variant="secondary" onClick={handleLogout} aria-label="Cerrar sesión">
                            Cerrar Sesión
                        </Button>
                    </div>

                    {/* Barra de búsqueda y botón crear */}
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1">
                            <Input
                                name="search"
                                type="text"
                                placeholder="🔍 Buscar usuarios por nombre o correo..."
                                value={searchQuery}
                                onChange={(e) => handleSearch(e.target.value)}
                                aria-label="Buscar usuarios"
                            />
                        </div>
                        <Button onClick={() => setShowCreateModal(true)} aria-label="Crear nuevo usuario">
                            + Nuevo Usuario
                        </Button>
                    </div>

                    {/* Código de respaldo del Admin */}
                    <div className={`mt-4 p-4 rounded-lg ${hasExistingBackupCode ? 'bg-green-500/10 border border-green-500/20' : 'bg-amber-500/10 border border-amber-500/20'}`}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <svg className={`w-5 h-5 ${hasExistingBackupCode ? 'text-green-400' : 'text-amber-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                </svg>
                                <div>
                                    <span className={`text-sm font-medium ${hasExistingBackupCode ? 'text-green-400' : 'text-amber-400'}`}>
                                        Código de Respaldo
                                    </span>
                                    <p className="text-xs text-gray-500">
                                        Estado: {hasExistingBackupCode ? (
                                            <span className="text-green-400">✓ Configurado</span>
                                        ) : (
                                            <span className="text-amber-400">⚠️ No configurado</span>
                                        )}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                {backupCode && (
                                    <code className="bg-gray-800 px-3 py-1 rounded font-mono text-green-400 text-sm">
                                        {backupCode}
                                    </code>
                                )}
                                <Button
                                    variant="secondary"
                                    className={`text-xs py-1 px-3 ${hasExistingBackupCode ? 'bg-green-500/20 hover:bg-green-500/30 text-green-400' : 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400'}`}
                                    onClick={handleGenerateBackupCode}
                                    isLoading={generatingCode}
                                >
                                    {hasExistingBackupCode ? 'Regenerar' : 'Generar'} Código
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
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
                        <div className="bg-orange-500/10 rounded-xl p-4 border border-orange-500/30">
                            <p className="text-3xl font-bold text-orange-400">{stats.users_pending_face_registration}</p>
                            <p className="text-gray-400 text-sm">Rostro pendiente</p>
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
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Rol</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Rostro</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Estado</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {paginatedUsers.map((user) => (
                                        <tr key={user.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                                            <td className="py-3 px-4 text-white font-medium">{user.username}</td>
                                            <td className="py-3 px-4 text-gray-300">{user.email || '-'}</td>
                                            <td className="py-3 px-4">
                                                <span className={`px-2 py-1 text-xs rounded-full ${user.role === 'auditor'
                                                    ? 'bg-purple-500/10 text-purple-400'
                                                    : 'bg-blue-500/10 text-blue-400'
                                                    }`}>
                                                    {user.role}
                                                </span>
                                            </td>
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
                                                        ⚠️ Reset pass
                                                    </span>
                                                ) : (
                                                    <span className="px-2 py-1 text-xs bg-green-500/10 text-green-400 rounded-full">
                                                        ✓ Activo
                                                    </span>
                                                )}
                                            </td>
                                            <td className="py-3 px-4">
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="secondary"
                                                        className="text-xs py-1 px-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400"
                                                        onClick={() => openEditModal(user)}
                                                        aria-label={`Editar usuario ${user.username}`}
                                                    >
                                                        ✏️ Editar
                                                    </Button>
                                                    {user.is_locked ? (
                                                        <>
                                                            <Button
                                                                variant="primary"
                                                                className="text-xs py-1 px-2"
                                                                onClick={() => handleUnlock(user.id, user.username)}
                                                                isLoading={processingUserId === user.id}
                                                            >
                                                                🔓
                                                            </Button>
                                                            <Button
                                                                variant="secondary"
                                                                className="text-xs py-1 px-2 bg-green-500/20 hover:bg-green-500/30 text-green-400"
                                                                onClick={() => handleEnable(user.id, user.username)}
                                                                isLoading={processingUserId === user.id}
                                                            >
                                                                ✓
                                                            </Button>
                                                        </>
                                                    ) : (
                                                        <Button
                                                            variant="secondary"
                                                            className="text-xs py-1 px-2 bg-red-500/20 hover:bg-red-500/30 text-red-400"
                                                            onClick={() => handleDisable(user.id, user.username)}
                                                            isLoading={processingUserId === user.id}
                                                        >
                                                            ✗
                                                        </Button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {paginatedUsers.length === 0 && (
                                        <tr>
                                            <td colSpan={6} className="py-8 text-center text-gray-400">
                                                {searchQuery ? 'No se encontraron usuarios' : 'No hay usuarios registrados'}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination Controls */}
                        {totalPages > 1 && (
                            <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-700">
                                <p className="text-sm text-gray-400">
                                    Mostrando {((currentPage - 1) * USERS_PER_PAGE) + 1} - {Math.min(currentPage * USERS_PER_PAGE, filteredUsers.length)} de {filteredUsers.length} usuarios
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="secondary"
                                        className="text-sm"
                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                        disabled={currentPage <= 1}
                                    >
                                        ← Anterior
                                    </Button>
                                    <span className="py-2 px-4 text-gray-400 text-sm">
                                        Página {currentPage} de {totalPages}
                                    </span>
                                    <Button
                                        variant="secondary"
                                        className="text-sm"
                                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                        disabled={currentPage >= totalPages}
                                    >
                                        Siguiente →
                                    </Button>
                                </div>
                            </div>
                        )}
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

            {/* Modal Crear Usuario */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <Card className="w-full max-w-md">
                        <CardHeader>
                            <CardTitle>Crear Nuevo Usuario</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleCreateUser} className="space-y-4">
                                <Input
                                    label="Nombre de usuario"
                                    name="username"
                                    type="text"
                                    value={newUserData.username}
                                    onChange={(e) => setNewUserData({ ...newUserData, username: e.target.value })}
                                    placeholder="usuario123"
                                    required
                                    aria-required="true"
                                />
                                {/* Info sobre contraseña por defecto */}
                                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                                    <p className="text-sm text-amber-400">
                                        ⚠️ <strong>Contraseña temporal:</strong> El usuario recibirá como contraseña
                                        su mismo nombre de usuario. Deberá cambiarla en el primer inicio de sesión.
                                    </p>
                                </div>
                                <Input
                                    label="Email (opcional)"
                                    name="email"
                                    type="email"
                                    value={newUserData.email}
                                    onChange={(e) => setNewUserData({ ...newUserData, email: e.target.value })}
                                    placeholder="correo@ejemplo.com"
                                />
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-300">Rol</label>
                                    <select
                                        className="w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-violet-500"
                                        value={newUserData.role}
                                        onChange={(e) => setNewUserData({ ...newUserData, role: e.target.value })}
                                        aria-label="Seleccionar rol del usuario"
                                    >
                                        <option value="user">Usuario</option>
                                        <option value="auditor">Auditor</option>
                                    </select>
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        className="flex-1"
                                        onClick={() => {
                                            setShowCreateModal(false);
                                            setNewUserData({ username: '', email: '', role: 'user' });
                                        }}
                                    >
                                        Cancelar
                                    </Button>
                                    <Button type="submit" className="flex-1" isLoading={loading}>
                                        Crear Usuario
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Modal Editar Usuario */}
            {showEditModal && editingUser && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <Card className="w-full max-w-md">
                        <CardHeader>
                            <CardTitle>Editar Usuario: {editingUser.username}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleEditUser} className="space-y-4">
                                <Input
                                    label="Email"
                                    name="email"
                                    type="email"
                                    value={editingUser.email || ''}
                                    onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                                    placeholder="correo@ejemplo.com"
                                />
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-300">Rol</label>
                                    <select
                                        className="w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-violet-500"
                                        value={editingUser.role}
                                        onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                                        aria-label="Cambiar rol del usuario"
                                    >
                                        <option value="user">Usuario</option>
                                        <option value="auditor">Auditor</option>
                                    </select>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <input
                                        type="checkbox"
                                        id="requiresReset"
                                        checked={editingUser.requires_password_reset}
                                        onChange={(e) => setEditingUser({ ...editingUser, requires_password_reset: e.target.checked })}
                                        className="w-4 h-4 text-violet-500 bg-gray-800 border-gray-600 rounded focus:ring-violet-500"
                                    />
                                    <label htmlFor="requiresReset" className="text-sm text-gray-300">
                                        Requiere cambio de contraseña
                                    </label>
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        className="flex-1"
                                        onClick={() => {
                                            setShowEditModal(false);
                                            setEditingUser(null);
                                        }}
                                    >
                                        Cancelar
                                    </Button>
                                    <Button type="submit" className="flex-1" isLoading={loading}>
                                        Guardar Cambios
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}

