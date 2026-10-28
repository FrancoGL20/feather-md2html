#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Installer, Uninstaller, and Distribution Mechanisms.
Validates zero-bloatware distribution, PowerShell shortcut management,
path handling, exceptional cases, and system integrity.
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path

# Ensure app directory is in sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from tests.test_helpers import IsolatedEnvironmentTestCase


class TestInstallerAndDistributionIntegrity(IsolatedEnvironmentTestCase):
    """Pruebas de integridad de archivos y estructura de distribución."""

    def test_distribution_essential_files_present(self):
        """Verificar que todos los archivos esenciales para el instalador existan."""
        essential_files = [
            APP_DIR / "instalar.bat",
            APP_DIR / "desinstalar.bat",
            APP_DIR / "install_shortcuts.ps1",
            APP_DIR / "run.bat",
            APP_DIR / "launch.vbs",
            APP_DIR / "app.py",
            APP_DIR / "md_engine.py",
            APP_DIR / "math_engine.py",
            APP_DIR / "tray_manager.py",
            APP_DIR / "config.template.json",
            APP_DIR / "ui" / "index.html",
            APP_DIR / "ui" / "styles.css",
            APP_DIR / "ui" / "app.js",
            APP_DIR / "md2html" / "__init__.py",
            APP_DIR / "md2html" / "core" / "models.py",
            APP_DIR / "md2html" / "core" / "ports.py",
            APP_DIR / "md2html" / "adapters" / "http" / "router.py",
            APP_DIR / "md2html" / "templates" / "loader.py",
            APP_DIR / "assets" / "app_icon.ico",
        ]
        for f in essential_files:
            self.assertTrue(f.exists(), f"El archivo esencial de distribución no existe: {f}")
            self.assertGreater(f.stat().st_size, 0, f"El archivo está vacío: {f}")

    def test_instalar_bat_structure_and_safety(self):
        """Validar directivas críticas, codificación y seguridad en instalar.bat."""
        bat_path = APP_DIR / "instalar.bat"
        content = bat_path.read_text(encoding="utf-8", errors="ignore")

        # Codificación UTF-8 nativa en consola Windows
        self.assertIn("chcp 65001", content)
        # Definición segura en espacio de usuario (%LOCALAPPDATA%)
        self.assertIn("%LOCALAPPDATA%\\Programs\\MarkdownToHTML_App", content)
        # Detección de pythonw y python
        self.assertIn("pythonw", content)
        self.assertIn("python", content)
        # Asistencia amigable con winget si no existe Python
        self.assertIn("winget", content)
        # Bypass de execution policy de PowerShell para evitar bloqueos
        self.assertIn("-ExecutionPolicy Bypass", content)
        # Exclusión de archivos sensibles/temporales en el copiado
        self.assertIn(".git", content)
        self.assertIn("__pycache__", content)
        self.assertIn("config.json", content)

    def test_desinstalar_bat_safety_and_preservation(self):
        """Validar que desinstalar.bat preserve los documentos del usuario."""
        bat_path = APP_DIR / "desinstalar.bat"
        content = bat_path.read_text(encoding="utf-8", errors="ignore")

        # Codificación UTF-8
        self.assertIn("chcp 65001", content)
        # Confirmación interactiva antes de eliminar
        self.assertIn("CONFIRM", content)
        # Invocación de desinstalación de accesos directos
        self.assertIn("-Uninstall", content)
        # Aclaración explícita de preservación de documentos
        self.assertTrue(
            "Descargas" in content or "Downloads" in content or "no seran eliminados" in content,
            "El desinstalador debe advertir que los documentos del usuario se preservan"
        )

    def test_config_template_is_pure_and_portable(self):
        """Asegurar que config.template.json no tenga rutas absolutas quemadas."""
        template_path = APP_DIR / "config.template.json"
        data = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("root_dir"), "", "root_dir en la plantilla debe ser vacío para adaptarse a cada PC")
        self.assertEqual(data.get("recent_conversions"), [], "El historial en la plantilla debe estar vacío")

    def test_gitignore_protects_config_json(self):
        """Verificar que config.json esté en .gitignore para evitar fugas entre PCs."""
        gitignore_path = APP_DIR / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        self.assertIn("config.json", content)


class TestShortcutsScriptExecution(unittest.TestCase):
    """Pruebas funcionales de ejecución del script PowerShell en Windows."""

    @unittest.skipUnless(sys.platform == "win32", "Pruebas exclusivas para entorno Windows")
    def test_powershell_parameters_declared(self):
        """Verificar que install_shortcuts.ps1 declare -AppDirectory y -Uninstall."""
        ps1_path = APP_DIR / "install_shortcuts.ps1"
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            f"(Get-Command '{ps1_path}').Parameters.Keys"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(res.returncode, 0, f"Error inspeccionando script PowerShell: {res.stderr}")
        params = [p.strip().lower() for p in res.stdout.split()]
        self.assertIn("appdirectory", params)
        self.assertIn("uninstall", params)

    @unittest.skipUnless(sys.platform == "win32", "Pruebas exclusivas para entorno Windows")
    def test_shortcuts_creation_and_removal_in_isolated_dirs(self):
        """Simular creación y eliminación de accesos directos con WScript.Shell en carpetas temporales."""
        with tempfile.TemporaryDirectory(prefix="md2html_sc_") as tmp_dir:
            temp_path = Path(tmp_dir)
            mock_desktop = temp_path / "Desktop"
            mock_programs = temp_path / "Programs"
            mock_app_dir = temp_path / "InstalledApp"
            mock_assets = mock_app_dir / "assets"

            mock_desktop.mkdir()
            mock_programs.mkdir()
            mock_assets.mkdir(parents=True)

            # Copiar icono de prueba
            shutil.copy2(APP_DIR / "assets" / "app_icon.ico", mock_assets / "app_icon.ico")

            # Script de prueba aislado que usa la misma lógica de install_shortcuts.ps1
            ps_test_script = f"""
            $ErrorActionPreference = "Stop"
            $appDir = "{mock_app_dir}"
            $icoPath = Join-Path $appDir "assets\\app_icon.ico"
            $desktopLnk = "{mock_desktop}\\Markdown to HTML.lnk"
            $startLnk = "{mock_programs}\\Markdown to HTML.lnk"
            $pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
            if (-not $pythonw) {{ $pythonw = (Get-Command python).Source }}

            $wsh = New-Object -ComObject WScript.Shell

            # 1. Crear
            $sc1 = $wsh.CreateShortcut($desktopLnk)
            $sc1.TargetPath = $pythonw
            $sc1.Arguments = "app.py"
            $sc1.WorkingDirectory = $appDir
            if (Test-Path $icoPath) {{ $sc1.IconLocation = "$icoPath,0" }}
            $sc1.Save()

            $sc2 = $wsh.CreateShortcut($startLnk)
            $sc2.TargetPath = $pythonw
            $sc2.Arguments = "app.py"
            $sc2.WorkingDirectory = $appDir
            if (Test-Path $icoPath) {{ $sc2.IconLocation = "$icoPath,0" }}
            $sc2.Save()

            Write-Output "CREATED_SUCCESS"
            """

            # 1. Probar Creación
            cmd_create = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_test_script]
            res_create = subprocess.run(cmd_create, capture_output=True, text=True, timeout=10)
            self.assertEqual(res_create.returncode, 0, f"Fallo al crear accesos directos: {res_create.stderr}")
            self.assertIn("CREATED_SUCCESS", res_create.stdout)

            lnk_desktop = mock_desktop / "Markdown to HTML.lnk"
            lnk_programs = mock_programs / "Markdown to HTML.lnk"
            self.assertTrue(lnk_desktop.exists(), "El acceso directo de Escritorio no fue creado")
            self.assertTrue(lnk_programs.exists(), "El acceso directo de Menú Inicio no fue creado")

            # 2. Verificar propiedades del acceso directo creado
            ps_verify_script = f"""
            $wsh = New-Object -ComObject WScript.Shell
            $sc = $wsh.CreateShortcut("{lnk_desktop}")
            Write-Output "TARGET:$($sc.TargetPath)"
            Write-Output "ARGS:$($sc.Arguments)"
            Write-Output "WORKDIR:$($sc.WorkingDirectory)"
            """
            res_verify = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_verify_script],
                capture_output=True, text=True, timeout=10
            )
            self.assertIn("python", res_verify.stdout.lower())
            self.assertIn("ARGS:app.py", res_verify.stdout)
            self.assertIn(f"WORKDIR:{mock_app_dir}", res_verify.stdout)

            # 3. Probar Eliminación (Uninstall)
            ps_uninstall_script = f"""
            if (Test-Path "{lnk_desktop}") {{ Remove-Item "{lnk_desktop}" -Force }}
            if (Test-Path "{lnk_programs}") {{ Remove-Item "{lnk_programs}" -Force }}
            Write-Output "UNINSTALL_SUCCESS"
            """
            res_uninstall = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_uninstall_script],
                capture_output=True, text=True, timeout=10
            )
            self.assertEqual(res_uninstall.returncode, 0)
            self.assertIn("UNINSTALL_SUCCESS", res_uninstall.stdout)
            self.assertFalse(lnk_desktop.exists(), "El acceso directo de Escritorio debería haber sido eliminado")
            self.assertFalse(lnk_programs.exists(), "El acceso directo de Menú Inicio debería haber sido eliminado")

    @unittest.skipUnless(sys.platform == "win32", "Pruebas exclusivas para entorno Windows")
    def test_paths_with_spaces_handling(self):
        """Verificar manejo seguro de rutas con espacios en blanco en la instalación."""
        with tempfile.TemporaryDirectory(prefix="md2html spaces test_") as tmp_dir:
            spaced_path = Path(tmp_dir) / "Carpeta Con Espacios De Usuario"
            spaced_path.mkdir(parents=True)
            assets_dir = spaced_path / "assets"
            assets_dir.mkdir()
            shutil.copy2(APP_DIR / "assets" / "app_icon.ico", assets_dir / "app_icon.ico")

            # Ejecutar install_shortcuts pasando la ruta con espacios
            ps1_path = APP_DIR / "install_shortcuts.ps1"
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(ps1_path),
                "-AppDirectory", str(spaced_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(res.returncode, 0, f"Error manejando rutas con espacios: {res.stderr}")
            self.assertIn("Acceso directo", res.stdout)

    @unittest.skipUnless(sys.platform == "win32", "Pruebas exclusivas para entorno Windows")
    def test_uninstall_is_idempotent(self):
        """Asegurar que ejecutar uninstall múltiples veces consecutivas no lance error."""
        ps1_path = APP_DIR / "install_shortcuts.ps1"
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(ps1_path),
            "-Uninstall"
        ]
        # Primera ejecución
        res1 = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(res1.returncode, 0)

        # Segunda ejecución (idempotente)
        res2 = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(res2.returncode, 0)
        self.assertIn("No se encontraron accesos directos previos para eliminar", res2.stdout)

        # Reinstalar para restaurar el entorno del usuario
        cmd_reinstall = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(ps1_path),
            "-AppDirectory", str(APP_DIR)
        ]
        subprocess.run(cmd_reinstall, capture_output=True, text=True, timeout=10)


if __name__ == "__main__":
    unittest.main()
