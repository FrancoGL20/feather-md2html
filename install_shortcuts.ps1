$ErrorActionPreference = "Stop"

$appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$icoPath = Join-Path $appDir "assets\app_icon.ico"

# Detect pythonw.exe or python.exe
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    if (Test-Path "C:\Program Files\PyManager\pythonw.exe") {
        $pythonw = "C:\Program Files\PyManager\pythonw.exe"
    } else {
        $pythonw = (Get-Command python -ErrorAction SilentlyContinue).Source
    }
}

if (-not $pythonw) {
    Write-Error "No se encontro pythonw o python en el sistema."
    exit 1
}

$wshShell = New-Object -ComObject WScript.Shell

# 1. Desktop Shortcut
$desktopPath = [Environment]::GetFolderPath("Desktop")
$desktopLnk = Join-Path $desktopPath "Markdown to HTML.lnk"

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
$programsPath = [Environment]::GetFolderPath("Programs")
$startLnk = Join-Path $programsPath "Markdown to HTML.lnk"

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
