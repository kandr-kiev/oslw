# OSLW Wiki — Unified Launcher
# Об'єднує налаштування hostname та запуск системи
# Запуск: PowerShell ВІД ІМЕНІ АДМІНІСТРАТОРА
#
# Використання:
#   .\run-oslw.ps1           — запуск з адмін правами (рекомендовано)
#   .\run-oslw.ps1 -nohostname — запуск без налаштування hostname
#   .\run-oslw.ps1 -restart  — перезапуск без rebuild
#   .\run-oslw.ps1 -stop     — зупинити систему

[CmdletBinding()]
param(
    [switch]$NoHostname,
    [switch]$Restart,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Конфігурація
# ============================================================================
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DOCKER_COMPOSE_FILE = Join-Path $PROJECT_DIR "docker-compose.yml"
$PORT_BACKEND = 8000
$PORT_FRONTEND = 5173
$PORT_NGINX = 80
$HOSTNAME = "oslw.local"
$HOSTS_PATH = "C:\Windows\System32\drivers\etc\hosts"

# ============================================================================
# Функції
# ============================================================================
function Write-Header {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  OSLW Wiki — Full Stack Web System" -ForegroundColor Cyan
    Write-Host "  Backend: FastAPI + React + Nginx" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param($Number, $Text, $Color = "Yellow")
    Write-Host "[$Number/6] $Text" -ForegroundColor $Color
}

function Write-Success {
    param($Text)
    Write-Host "  ✓ $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param($Text)
    Write-Host "  ✗ $Text" -ForegroundColor Red
}

function Write-Warning-Custom {
    param($Text)
    Write-Host "  ⚠ $Text" -ForegroundColor Yellow
}

# ============================================================================
# Перевірка адмін прав + автоматичний перезапуск
# ============================================================================
function Test-AdminRights {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Restart-WithAdminRights {
    if (Test-AdminRights) { return }
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Запит прав адміністратора" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Цей скрипт вимагає адмін права для налаштування hostname." -ForegroundColor White
    Write-Host "  Буде запущено новий PowerShell вікно з адмін правами." -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "Продовжити? (y/n)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host ""
        Write-Host "  Скасовано. Запустіть PowerShell ВІД ІМЕНІ АДМІНІСТРАТОРА." -ForegroundColor Yellow
        exit 0
    }
    
    # Перезапуск з адмін правами
    $runArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    if ($NoHostname) { $runArgs += "-NoHostname" }
    if ($Restart) { $runArgs += "-Restart" }
    if ($Stop) { $runArgs += "-Stop" }
    
    Start-Process powershell -Verb RunAs -ArgumentList $runArgs -ErrorAction SilentlyContinue
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  Перезапуск з адмін правами... Закриваю поточне вікно." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        exit 0
    } else {
        Write-Host ""
        Write-Host "  ✗ Не вдалося отримати адмін права." -ForegroundColor Red
        Write-Host "  Запустіть PowerShell ВІД ІМЕНІ АДМІНІСТРАТОРА вручну." -ForegroundColor Yellow
        Write-Host "  Win + X → Terminal (Admin)" -ForegroundColor Cyan
        exit 1
    }
}

# ============================================================================
# Крок 1: Налаштування hostname (hosts файл)
# ============================================================================
function Setup-Hostname {
    param($SkipIfNoAdmin = $false)
    
    Write-Step 1 "Налаштування hostname..."
    
    if ($NoHostname) {
        Write-Warning-Custom "Пропущено (-NoHostname)"
        return $true
    }
    
    # Перевірка адмін прав
    if (-not (Test-AdminRights)) {
        if ($SkipIfNoAdmin) {
            Write-Warning-Custom "Немає адмін прав — hostname не налаштовано"
            Write-Host "    Доступ буде тільки через http://localhost:80" -ForegroundColor Yellow
            return $true
        }
        return $false
    }
    
    try {
        $hostsContent = Get-Content $HOSTS_PATH
        $existing = $hostsContent | Where-Object { $_ -match "^127\.0\.0\.1\s+$HOSTNAME" }
        
        if ($existing) {
            Write-Success "Запис '$HOSTNAME' вже існує"
        } else {
            Write-Host "  Додаю запис у hosts файл..." -ForegroundColor Yellow
            
            if (-not (Test-Path $HOSTS_PATH)) {
                Write-Error-Custom "Файл hosts не знайдено: $HOSTS_PATH"
                return $false
            }
            
            Add-Content -Path $HOSTS_PATH -Value "`n127.0.0.1    $HOSTNAME"
            Write-Success "Додано: 127.0.0.1 -> $HOSTNAME"
        }
        
        # Очищення DNS кешу
        ipconfig /flushdns | Out-Null
        Write-Success "DNS кеш очищено"
        
        # Перевірка DNS
        try {
            $dnsResult = Resolve-DnsName $HOSTNAME -ErrorAction Stop
            Write-Success "DNS: $HOSTNAME -> $($dnsResult.IPAddress)"
        } catch {
            Write-Warning-Custom "DNS не знайдено (можливо, браузер треба перезавантажити)"
        }
        
        return $true
    } catch {
        Write-Error-Custom "Помилка налаштування hostname: $_"
        return $false
    }
}

# ============================================================================
# Крок 2: Зупинка системи
# ============================================================================
function Stop-System {
    Write-Header
    Write-Host "  Зупиняю OSLW Wiki..." -ForegroundColor Yellow
    
    try {
        cd $PROJECT_DIR
        docker compose -f $DOCKER_COMPOSE_FILE down 2>&1 | Out-Null
        Write-Success "Систему зупинено"
    } catch {
        Write-Error-Custom "Помилка зупинки: $_"
    }
    
    Write-Host ""
    Write-Host "  Готово. Запустіть: .\run-oslw.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

# ============================================================================
# Крок 3: Перевірка Docker
# ============================================================================
function Test-Docker {
    Write-Step 2 "Перевірка Docker..."
    
    try {
        $docker_version = docker --version
        Write-Success "$docker_version"
        
        docker info 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Docker не запущено. Запустіть Docker Desktop."
            return $false
        }
        Write-Success "Docker доступний"
        return $true
    } catch {
        Write-Error-Custom "Docker не знайдено. Встановіть Docker Desktop."
        Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        return $false
    }
}

# ============================================================================
# Крок 4: Перевірка проекту
# ============================================================================
function Test-Project {
    Write-Step 3 "Перевірка проекту..."
    
    if (-not (Test-Path $DOCKER_COMPOSE_FILE)) {
        Write-Error-Custom "docker-compose.yml не знайдено"
        Write-Host "  Шлях: $DOCKER_COMPOSE_FILE" -ForegroundColor Yellow
        return $false
    }
    Write-Success "docker-compose.yml знайдено"
    
    if (-not (Test-Path (Join-Path $PROJECT_DIR "src"))) {
        Write-Error-Custom "Папка src/ не знайдено"
        return $false
    }
    Write-Success "src/ знайдено"
    
    if (-not (Test-Path (Join-Path $PROJECT_DIR "frontend"))) {
        Write-Error-Custom "Папка frontend/ не знайдено"
        return $false
    }
    Write-Success "frontend/ знайдено"
    
    return $true
}

# ============================================================================
# Крок 5: Перевірка портів
# ============================================================================
function Test-Ports {
    Write-Step 4 "Перевірка портів..."
    
    $ports_free = $true
    
    foreach ($port in @($PORT_BACKEND, $PORT_FRONTEND, $PORT_NGINX)) {
        $listening = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
        if ($listening) {
            Write-Error-Custom "Порт $port зайнятий"
            $pid = ($listening -split ' ' | Where-Object { $_ -match '^\d+$' } | Select-Object -First 1)
            if ($pid) {
                Write-Host "    PID: $pid" -ForegroundColor Yellow
            }
            $ports_free = $false
        } else {
            Write-Success "Порт $port вільний"
        }
    }
    
    if (-not $ports_free) {
        Write-Host ""
        $release = Read-Host "Звільнити порти? (y/n)"
        if ($release -eq "y" -or $release -eq "Y") {
            foreach ($port in @($PORT_BACKEND, $PORT_FRONTEND, $PORT_NGINX)) {
                $proc = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
                if ($proc) {
                    $pid = ($proc -split ' ' | Where-Object { $_ -match '^\d+$' } | Select-Object -First 1)
                    if ($pid) {
                        Write-Host "  Зупиняю процес на порту $port (PID: $pid)..." -ForegroundColor Yellow
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    }
                }
            }
            Start-Sleep -Seconds 2
            Write-Success "Порти звільнено"
        } else {
            return $false
        }
    }
    
    return $true
}

# ============================================================================
# Крок 6: Запуск Docker Compose
# ============================================================================
function Start-Containers {
    Write-Step 5 "Запуск Docker Compose..."
    
    Write-Host ""
    
    if ($Restart) {
        Write-Host "  Перезапуск без rebuild..." -ForegroundColor Yellow
        try {
            cd $PROJECT_DIR
            docker compose -f $DOCKER_COMPOSE_FILE restart 2>&1 | Out-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Помилка перезапуску Docker Compose"
                return $false
            }
            Write-Success "Контейнери перезапущено"
        } catch {
            Write-Error-Custom "Помилка: $_"
            return $false
        }
    } else {
        Write-Host "  Запускаю контейнери з rebuild..." -ForegroundColor Yellow
        try {
            cd $PROJECT_DIR
            docker compose -f $DOCKER_COMPOSE_FILE down 2>&1 | Out-Null
            docker compose -f $DOCKER_COMPOSE_FILE up --build -d 2>&1 | Out-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Помилка запуску Docker Compose"
                return $false
            }
            Write-Success "Контейнери запущено"
        } catch {
            Write-Error-Custom "Помилка: $_"
            return $false
        }
    }
    
    return $true
}

# ============================================================================
# Чекаємо на готовність
# ============================================================================
function Wait-Healthy {
    Write-Host ""
    Write-Host "  Чекаю на готовність контейнерів..." -ForegroundColor Yellow
    
    $max_wait = 60
    $elapsed = 0
    
    while ($elapsed -lt $max_wait) {
        $backend_health = docker inspect --format='{{.State.Health.Status}}' oslw-backend 2>$null
        if ($backend_health -eq "healthy") {
            Write-Success "Backend готовий (healthy)"
            return $true
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "  . " -NoNewline -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Warning-Custom "Backend не став healthy за $max_wait секунд"
    Write-Host "  Перевірте логи: docker logs oslw-backend" -ForegroundColor Yellow
    Write-Host "  docker logs oslw-frontend" -ForegroundColor Yellow
    return $false
}

# ============================================================================
# Головний потік
# ============================================================================

# Спеціальний режим: зупинка
if ($Stop) {
    Stop-System
}

# Головний потік
Write-Header

# Крок 1: Admin права + hostname
if (-not (Test-AdminRights) -and -not $NoHostname) {
    Write-Host ""
    Write-Host "  ⚠ Потрібні права адміністратора для налаштування hostname." -ForegroundColor Yellow
    Write-Host "  Перезапуск з UAC elevation..." -ForegroundColor Cyan
    $runArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    if ($Restart) { $runArgs += "-Restart" }
    if ($Stop) { $runArgs += "-Stop" }
    
    Start-Process powershell -Verb RunAs -ArgumentList $runArgs
    exit 0
}

# Якщо -NoHostname — пропускаємо налаштування hostname
if (-not $NoHostname) {
    $hostname_ok = Setup-Hostname
} else {
    Write-Step 1 "Hostname пропущено (-NoHostname)"
    $hostname_ok = $false
}

# Крок 2: Docker
if (-not (Test-Docker)) { exit 1 }

# Крок 3: Проект
if (-not (Test-Project)) { exit 1 }

# Крок 4: Порти
if (-not (Test-Ports)) { exit 1 }

# Крок 5: Запуск
if (-not (Start-Containers)) { exit 1 }

# Чекаємо на готовність
if (-not (Wait-Healthy)) {
    Write-Host ""
    Write-Warning-Custom "Backend не healthy, але продовжую..."
}

# Крок 6: Фінальний екран
Write-Step 6 "Готово!"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  OSLW Wiki — Систему готово!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($HOSTNAME -and $hostname_ok) {
    Write-Host "  🌐 Веб-інтерфейс:    http://$HOSTNAME" -ForegroundColor Green
} else {
    Write-Host "  🌐 Веб-інтерфейс:    http://localhost:$PORT_NGINX" -ForegroundColor Green
    Write-Host "    (hostname не налаштовано — потрібне адмін права)" -ForegroundColor Yellow
}

Write-Host "  🔌 API (прямий):      http://localhost:$PORT_BACKEND" -ForegroundColor Yellow
Write-Host "  ⚛️  Frontend (dev):    http://localhost:$PORT_FRONTEND" -ForegroundColor Magenta
Write-Host ""
Write-Host "  API Endpoints:" -ForegroundColor Cyan
Write-Host "    GET  /health              — Перевірка здоров'я" -ForegroundColor White
Write-Host "    GET  /api/pages           — Список усіх сторінок" -ForegroundColor White
Write-Host "    GET  /api/pages/{slug}    — Конкретна сторінка" -ForegroundColor White
Write-Host "    GET  /api/stats           — Статистика wiki" -ForegroundColor White
Write-Host "    GET  /api/search?q=...    — Пошук" -ForegroundColor White
Write-Host ""
Write-Host "  Керування:" -ForegroundColor Cyan
Write-Host "    docker compose logs -f    — Логи" -ForegroundColor White
Write-Host "    .\run-oslw.ps1 -stop      — Зупинити" -ForegroundColor White
Write-Host "    .\run-oslw.ps1 -restart   — Перезапустити" -ForegroundColor White
Write-Host ""
Write-Host "  Файли проекту: $PROJECT_DIR" -ForegroundColor Gray
Write-Host ""

# Пропонуємо відкрити браузер
$open_browser = Read-Host "Відкрити веб-інтерфейс в браузері? (y/n)"
if ($open_browser -eq "y" -or $open_browser -eq "Y") {
    $url = if ($hostname_ok) { "http://$HOSTNAME" } else { "http://localhost:$PORT_NGINX" }
    try {
        Start-Process $url
        Write-Success "Браузер відкрито!"
    } catch {
        Write-Host "  Відкрийте вручну: $url" -ForegroundColor Yellow
    }
}
