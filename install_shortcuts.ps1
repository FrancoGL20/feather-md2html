param(
    [string]$AppDirectory = "",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$desktopPath = [Environment]::GetFolderPath("Desktop")
$desktopLnk = Join-Path $desktopPath "Markdown to HTML.lnk"

$programsPath = [Environment]::GetFolderPath("Programs")
$startLnk = Join-Path $programsPath "Markdown to HTML.lnk"

# 1. Modo Desinstalacion
if ($Uninstall) {
    $removed = 0
    if (Test-Path $desktopLnk) {
        Remove-Item -Path $desktopLnk -Force -ErrorAction SilentlyContinue
        Write-Output "Acceso directo en Escritorio eliminado."
        $removed++
    }
    if (Test-Path $startLnk) {
        Remove-Item -Path $startLnk -Force -ErrorAction SilentlyContinue
        Write-Output "Acceso directo en Menu Inicio eliminado."
        $removed++
    }
    if ($removed -eq 0) {
        Write-Output "No se encontraron accesos directos previos para eliminar."
    }
    exit 0
}

# 2. Modo Instalacion / Creacion de Accesos Directos
if ($AppDirectory -and (Test-Path $AppDirectory)) {
    $appDir = (Resolve-Path $AppDirectory).Path
} else {
    $appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$icoPath = Join-Path $appDir "assets\app_icon.ico"

# Deteccion robusta de pythonw.exe o python.exe
$pythonw = $null

# Intento 1: En PATH del sistema
$cmd = Get-Command pythonw -ErrorAction SilentlyContinue
if ($cmd) {
    $pythonw = $cmd.Source
}

# Intento 2: Rutas estandar de instalacion de Python en Windows
if (-not $pythonw) {
    $searchPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\pythonw.exe",
        "C:\Program Files\Python*\pythonw.exe",
        "C:\Program Files\PyManager\pythonw.exe",
        "$env:ProgramFiles\Python*\pythonw.exe"
    )
    foreach ($p in $searchPaths) {
        $found = Get-Item $p -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $pythonw = $found.FullName
            break
        }
    }
}

# Intento 3: Fallback a python.exe en PATH
if (-not $pythonw) {
    $cmdPy = Get-Command python -ErrorAction SilentlyContinue
    if ($cmdPy) {
        $pythonw = $cmdPy.Source
    }
}

if (-not $pythonw) {
    Write-Error "No se encontro pythonw.exe ni python.exe en el sistema."
    exit 1
}

$wshShell = New-Object -ComObject WScript.Shell

# 1. Desktop Shortcut
$shortcut = $wshShell.CreateShortcut($desktopLnk)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "app.py"
$shortcut.WorkingDirectory = $appDir
$shortcut.Description = "Conversor de Markdown a HTML Ultraligero y Rapido"
if (Test-Path $icoPath) {
    $shortcut.IconLocation = "$icoPath,0"
}
$shortcut.Save()
Write-Output "Acceso directo en Escritorio creado: $desktopLnk"

# 2. Start Menu Programs Shortcut
$startShortcut = $wshShell.CreateShortcut($startLnk)
$startShortcut.TargetPath = $pythonw
$startShortcut.Arguments = "app.py"
$startShortcut.WorkingDirectory = $appDir
$startShortcut.Description = "Conversor de Markdown a HTML Ultraligero y Rapido"
if (Test-Path $icoPath) {
    $startShortcut.IconLocation = "$icoPath,0"
}
$startShortcut.Save()
Write-Output "Acceso directo en Menu Inicio creado: $startLnk"
