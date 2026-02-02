'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from '@/components';
import Cookies from 'js-cookie';

// Token secreto para auditoría - diferente al de admin
const DEVICE_SECRET_KEY = 'audit_device_token_v1';
const MASTER_DEVICE_TOKEN = 'BQUISPE-LAPTOP-2026-AUDITORIA-TOKEN-SECURE';

interface AuditLog {
    id: number;
    action: string;
    admin_id: number | null;
    admin_username: string;
    target_user_id: number | null;
    target_username: string;
    details: string;
    ip_address: string;
    user_agent: string;
    location_country: string;
    location_city: string;
    location_region: string;
    created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
    'user_disabled': { label: '🔒 Usuario Deshabilitado', color: 'text-red-400' },
    'user_enabled': { label: '✓ Usuario Habilitado', color: 'text-green-400' },
    'user_unlocked': { label: '🔓 Usuario Desbloqueado', color: 'text-yellow-400' },
    'admin_login': { label: '🔑 Login Admin', color: 'text-blue-400' },
};

export default function AuditPage() {
    const router = useRouter();
    const [deviceAuthorized, setDeviceAuthorized] = useState<boolean | null>(null);
    const [showDeviceSetup, setShowDeviceSetup] = useState(false);
    const [deviceTokenInput, setDeviceTokenInput] = useState('');
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loginData, setLoginData] = useState({ username: '', password: '' });
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [totalLogs, setTotalLogs] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Estado para código de respaldo del auditor
    const [backupCode, setBackupCode] = useState<string | null>(null);
    const [generatingCode, setGeneratingCode] = useState(false);
    const [hasExistingBackupCode, setHasExistingBackupCode] = useState<boolean>(false);

    useEffect(() => {
        checkDeviceAuthorization();
    }, []);

    const checkDeviceAuthorization = () => {
        const storedToken = localStorage.getItem(DEVICE_SECRET_KEY);

        if (storedToken === MASTER_DEVICE_TOKEN) {
            setDeviceAuthorized(true);
            const token = Cookies.get('access_token');
            if (token) {
                setIsAuthenticated(true);
                fetchLogs(token, 1);
                fetchBackupCodeStatus(token);
            } else {
                router.push('/login');
            }
        } else if (!storedToken) {
            setShowDeviceSetup(true);
            setDeviceAuthorized(false);
        } else {
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
                // Ya tiene sesión, cargar datos del auditor
                setIsAuthenticated(true);
                fetchLogs(token, 1);
                fetchBackupCodeStatus(token);
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

    const fetchLogs = async (token: string, page: number) => {
        try {
            setLoading(true);

            // Verificar rol primero
            const statsRes = await fetch(`${API_URL}/api/audit/stats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!statsRes.ok) {
                setError('Acceso denegado. Se requiere rol de auditor.');
                setIsAuthenticated(false);
                return;
            }

            const response = await fetch(`${API_URL}/api/audit/logs?page=${page}&limit=20`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (data.success) {
                setLogs(data.logs);
                setTotalLogs(data.total);
                setCurrentPage(page);
            }
        } catch (err) {
            console.error('Error fetching logs:', err);
            setError('Error de conexión o sesión inválida');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        Cookies.remove('audit_token');
        Cookies.remove('access_token');
        setIsAuthenticated(false);
        setLogs([]);
        router.push('/login');
    };

    // Generar código de respaldo para el auditor
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
                setSuccess('¡Código de respaldo generado!');
            } else {
                setError(data.message || 'Error al generar código');
            }
        } catch {
            setError('Error de conexión');
        } finally {
            setGeneratingCode(false);
        }
    };

    const formatDate = (isoString: string) => {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleString('es-EC', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Pantalla de acceso denegado
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
                        <p className="text-gray-400">Este dispositivo no está autorizado para auditoría.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Pantalla de configuración de dispositivo
    if (showDeviceSetup) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 mb-4">
                                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <CardTitle>Panel de Auditoría</CardTitle>
                            <p className="text-gray-400 text-sm mt-2">Ingrese el token de auditor</p>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleDeviceSetup} className="space-y-4">
                            <Input
                                label="Token de Auditoría"
                                type="password"
                                value={deviceTokenInput}
                                onChange={(e) => setDeviceTokenInput(e.target.value)}
                                placeholder="Ingrese el token..."
                            />
                            {error && (
                                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                                    {error}
                                </div>
                            )}
                            <Button type="submit" className="w-full">
                                Autorizar Dispositivo
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Pantalla de verificación
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
                            <p className="text-xs text-green-400 mt-2">✓ Dispositivo autorizado</p>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-center text-gray-400">
                            {error ? (
                                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                                    {error}
                                    <Button
                                        className="mt-2 w-full"
                                        variant="secondary"
                                        onClick={() => router.push('/login')}
                                    >
                                        Ir al Login
                                    </Button>
                                </div>
                            ) : (
                                <div>
                                    <p>Validando credenciales de auditor...</p>
                                    <Button
                                        className="mt-4 w-full"
                                        variant="secondary"
                                        onClick={() => router.push('/login')}
                                    >
                                        Ir al Login Ahora
                                    </Button>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Panel de auditoría
    return (
        <div className="min-h-screen p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">📋 Panel de Auditoría</h1>
                        <p className="text-gray-400 mt-1">Registro de acciones administrativas</p>
                    </div>
                    <Button variant="secondary" onClick={handleLogout}>
                        Cerrar Sesión
                    </Button>
                </div>

                {/* Código de respaldo del Auditor */}
                <div className="mb-6 p-4 rounded-lg bg-gray-800/50 border border-gray-700">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                            </svg>
                            <div>
                                <span className="text-sm font-medium text-white">
                                    Código de Respaldo
                                </span>
                                <p className="text-xs text-gray-500">
                                    Uso ilimitado hasta generar uno nuevo
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
                                className="text-xs py-1 px-3 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400"
                                onClick={handleGenerateBackupCode}
                                isLoading={generatingCode}
                            >
                                Generar Código
                            </Button>
                        </div>
                    </div>
                    {success && <p className="mt-2 text-xs text-green-400">{success}</p>}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/30">
                        <p className="text-3xl font-bold text-blue-400">{totalLogs}</p>
                        <p className="text-gray-400 text-sm">Registros totales</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                        <p className="text-3xl font-bold text-white">{logs.length}</p>
                        <p className="text-gray-400 text-sm">En esta página</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                        <p className="text-3xl font-bold text-white">{currentPage}</p>
                        <p className="text-gray-400 text-sm">Página actual</p>
                    </div>
                </div>

                {/* Logs Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Historial de Acciones</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-700">
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Fecha</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Acción</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Admin</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Usuario Afectado</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">IP</th>
                                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Ubicación</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((log) => (
                                        <tr key={log.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                                            <td className="py-3 px-4 text-gray-300 text-sm">
                                                {formatDate(log.created_at)}
                                            </td>
                                            <td className="py-3 px-4">
                                                <span className={ACTION_LABELS[log.action]?.color || 'text-gray-400'}>
                                                    {ACTION_LABELS[log.action]?.label || log.action}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-white font-medium">
                                                {log.admin_username}
                                            </td>
                                            <td className="py-3 px-4 text-gray-300">
                                                {log.target_username || '-'}
                                            </td>
                                            <td className="py-3 px-4">
                                                <code className="text-xs bg-gray-700 px-2 py-1 rounded">
                                                    {log.ip_address}
                                                </code>
                                            </td>
                                            <td className="py-3 px-4 text-gray-300 text-sm">
                                                {log.location_city && log.location_country
                                                    ? `${log.location_city}, ${log.location_country}`
                                                    : log.location_country || '-'}
                                            </td>
                                        </tr>
                                    ))}
                                    {logs.length === 0 && !loading && (
                                        <tr>
                                            <td colSpan={6} className="py-8 text-center text-gray-400">
                                                No hay registros de auditoría
                                            </td>
                                        </tr>
                                    )}
                                    {loading && (
                                        <tr>
                                            <td colSpan={6} className="py-8 text-center text-gray-400">
                                                Cargando...
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        {totalLogs > 0 && (
                            <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-700">
                                <p className="text-sm text-gray-400">
                                    Mostrando {((currentPage - 1) * 20) + 1} - {Math.min(currentPage * 20, totalLogs)} de {totalLogs} registros
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="secondary"
                                        className="text-sm"
                                        onClick={() => fetchLogs(Cookies.get('access_token') || Cookies.get('audit_token') || '', currentPage - 1)}
                                        disabled={currentPage <= 1 || loading}
                                    >
                                        ← Anterior
                                    </Button>
                                    <span className="py-2 px-4 text-gray-400">
                                        Página {currentPage} de {Math.ceil(totalLogs / 20)}
                                    </span>
                                    <Button
                                        variant="secondary"
                                        className="text-sm"
                                        onClick={() => fetchLogs(Cookies.get('access_token') || Cookies.get('audit_token') || '', currentPage + 1)}
                                        disabled={currentPage >= Math.ceil(totalLogs / 20) || loading}
                                    >
                                        Siguiente →
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Info */}
                <div className="mt-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700">
                    <h3 className="text-lg font-semibold text-white mb-3">ℹ️ Información de Auditoría</h3>
                    <div className="text-sm text-gray-400 space-y-2">
                        <p>• Todas las acciones del administrador son registradas automáticamente</p>
                        <p>• La IP se captura usando headers de proxy (X-Forwarded-For)</p>
                        <p>• La ubicación se obtiene de la API ip-api.com</p>
                        <p>• Los logs no pueden ser eliminados ni modificados</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
