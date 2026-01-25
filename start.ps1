# Script de inicio rápido para Login Seguro
# Ejecutar desde la raíz del proyecto con: .\start.ps1

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   LOGIN SEGURO - Iniciando servicios..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
Write-Host "[1/4] Verificando Docker..." -ForegroundColor Yellow
$dockerRunning = docker info 2>$null
if (-not $?) {
    Write-Host "ERROR: Docker no está corriendo. Por favor, inicie Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "Docker OK" -ForegroundColor Green

# Iniciar PostgreSQL
Write-Host "[2/4] Iniciando PostgreSQL con Docker..." -ForegroundColor Yellow
docker-compose up -d
Start-Sleep -Seconds 5
Write-Host "PostgreSQL iniciado en puerto 5432" -ForegroundColor Green

# Iniciar Backend
Write-Host "[3/4] Iniciando Backend (Puerto 3000)..." -ForegroundColor Yellow
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd back; if (Test-Path venv) { .\venv\Scripts\activate }; uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload" -PassThru
Write-Host "Backend iniciando..." -ForegroundColor Green

# Iniciar Frontend
Write-Host "[4/4] Iniciando Frontend (Puerto 3001)..." -ForegroundColor Yellow
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd front; npm run dev -- -p 3001" -PassThru
Write-Host "Frontend iniciando..." -ForegroundColor Green

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Servicios iniciados correctamente!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs de acceso:" -ForegroundColor White
Write-Host "  Frontend:    http://localhost:3001" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API Docs:    http://localhost:3000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presione Ctrl+C para detener todos los servicios" -ForegroundColor Yellow
