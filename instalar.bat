@echo off
chcp 65001 >nul
title Markdown to HTML — Instalador Rapido
cls

echo ======================================================================
echo   Markdown to HTML Desktop App — Instalador Rapido (1 Clic)
echo   Arquitectura: Zero-Bloatware ^| Nativo para Windows
echo ======================================================================
echo.

rem 1. Deteccion de Python
set "PYTHON_FOUND="

where pythonw >nul 2>nul
if %errorlevel% equ 0 set "PYTHON_FOUND=1"

if not defined PYTHON_FOUND (
    where python >nul 2>nul
    if %errorlevel% equ 0 set "PYTHON_FOUND=1"
)

if not defined PYTHON_FOUND (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%D\pythonw.exe" set "PYTHON_FOUND=1"
        if exist "%%D\python.exe" set "PYTHON_FOUND=1"
    )
    for /d %%D in ("C:\Program Files\Python*") do (
        if exist "%%D\pythonw.exe" set "PYTHON_FOUND=1"
        if exist "%%D\python.exe" set "PYTHON_FOUND=1"
    )
    if exist "C:\Program Files\PyManager\pythonw.exe" set "PYTHON_FOUND=1"
)

if not defined PYTHON_FOUND (
    echo [AVISO] No se detecto Python instalado en el sistema.
    echo Esta aplicacion funciona con el runtime nativo de Python 3.8+ (Zero-Bloatware).
    echo.
    echo ¿Deseas instalar Python 3.12 automaticamente mediante winget?
    echo   [S] Si, instalar Python ahora
    echo   [N] No, cancelar instalacion
    echo.
    set /p "INSTALL_PY=Tu eleccion (S/N): "
    if /I "%INSTALL_PY%"=="S" (
        echo.
        echo Ejecutando instalacion de Python via winget...
        winget install -e --id Python.Python.3.12 --scope user
        echo.
        echo Una vez finalizada la instalacion de Python, vuelve a ejecutar este instalador.
        pause
        exit /b 0
    ) else (
        echo Instalacion cancelada. Puedes descargar Python manualmente desde python.org
        pause
        exit /b 1
    )
)

rem 2. Definicion de ruta de instalacion en espacio de usuario (sin requerir permisos de Admin)
set "TARGET_DIR=%LOCALAPPDATA%\Programs\MarkdownToHTML_App"
set "SOURCE_DIR=%~dp0"
rem Quitar barra invertida final si existe
if "%SOURCE_DIR:~-1%"=="\" set "SOURCE_DIR=%SOURCE_DIR:~0,-1%"

echo [1/3] Verificando ruta de instalacion...
echo       Destino: %TARGET_DIR%
echo.

rem Si ya estamos ejecutando dentro de TARGET_DIR, solo actualizar accesos directos
if /I "%SOURCE_DIR%"=="%TARGET_DIR%" (
    echo Ya se encuentra en el directorio de instalacion. Actualizando accesos directos...
    goto CREAR_ACCESOS
)

echo [2/3] Copiando archivos de la aplicacion...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

rem Copiar archivos excluyendo temporales, git y logs
robocopy "%SOURCE_DIR%" "%TARGET_DIR%" /E /XD .git __pycache__ test_output_library tmp /XF *.pyc debug_log.txt config.json >nul
if %errorlevel% gtr 7 (
    echo [ERROR] No se pudieron copiar todos los archivos a %TARGET_DIR%.
    pause
    exit /b 1
)

:CREAR_ACCESOS
echo [3/3] Registrando accesos directos en Escritorio y Menu Inicio...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%TARGET_DIR%\install_shortcuts.ps1" -AppDirectory "%TARGET_DIR%"
if %errorlevel% neq 0 (
    echo [AVISO] Ocurrio una advertencia creando los accesos directos.
)

echo.
echo ======================================================================
echo   ¡Instalacion completada exitosamente!
echo.
echo   - Acceso en Escritorio: "Markdown to HTML"
echo   - Acceso en Menu Inicio: Busca "Markdown to HTML"
echo   - Ubicacion permanente: %TARGET_DIR%
echo   - Desinstalador: %TARGET_DIR%\desinstalar.bat
echo ======================================================================
echo.

set /p "LAUNCH_NOW=¿Deseas abrir Markdown to HTML ahora? (S/N) [S]: "
if /I "%LAUNCH_NOW%"=="" set "LAUNCH_NOW=S"
if /I "%LAUNCH_NOW%"=="S" (
    start "" "%TARGET_DIR%\launch.vbs"
)

exit /b 0
