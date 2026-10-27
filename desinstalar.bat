@echo off
chcp 65001 >nul
title Markdown to HTML — Desinstalador
cls

echo ======================================================================
echo   Markdown to HTML Desktop App — Desinstalador
echo ======================================================================
echo.
echo Esta accion eliminara los accesos directos y los archivos del programa.
echo (Tus archivos HTML generados en Descargas no seran eliminados).
echo.

set /p "CONFIRM=¿Estas seguro de que deseas desinstalar la aplicacion? (S/N): "
if /I "%CONFIRM%" neq "S" (
    echo.
    echo Desinstalacion cancelada por el usuario.
    timeout /t 2 >nul
    exit /b 0
)

echo.
echo [1/2] Eliminando accesos directos del sistema...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_shortcuts.ps1" -Uninstall

echo.
echo [2/2] Eliminando archivos de la aplicacion...

set "CURRENT_DIR=%~dp0"
set "APP_INSTALL_DIR=%LOCALAPPDATA%\Programs\MarkdownToHTML_App\"

rem Si se ejecuta desde la carpeta instalada en LOCALAPPDATA, auto-eliminacion diferida
if /I "%CURRENT_DIR%"=="%APP_INSTALL_DIR%" (
    echo Limpiando directorio de instalacion...
    echo.
    echo ======================================================================
    echo   [OK] Markdown to HTML se ha desinstalado correctamente.
    echo ======================================================================
    echo.
    timeout /t 2 >nul
    start "" /b cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q \"%LOCALAPPDATA%\Programs\MarkdownToHTML_App\""
    exit /b 0
) else (
    rem Si se ejecuta desde el repositorio o carpeta externa
    if exist "%LOCALAPPDATA%\Programs\MarkdownToHTML_App" (
        rmdir /s /q "%LOCALAPPDATA%\Programs\MarkdownToHTML_App"
        echo Archivos eliminados de %%LOCALAPPDATA%%\Programs\MarkdownToHTML_App
    ) else (
        echo No se encontro instalacion previa en %%LOCALAPPDATA%%.
    )
    echo.
    echo ======================================================================
    echo   [OK] Accesos directos y registros eliminados correctamente.
    echo ======================================================================
    echo.
    pause
    exit /b 0
)
