#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitarios para el administrador del System Tray (tray_manager.py).
Valida estructuras Win32, ciclo de vida de hilos, callbacks y notificaciones sin bloatware.
"""

import sys
import time
import ctypes
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import tray_manager


class TestTrayManager(unittest.TestCase):
    def setUp(self):
        self.icon_path = APP_DIR / "assets" / "app_icon.ico"
        self.log_messages = []

    def _log(self, msg):
        self.log_messages.append(msg)

    def test_tray_structures_and_sizes(self):
        """Valida que las estructuras ctypes tengan tamaños correctos de 64-bit en Windows."""
        self.assertEqual(ctypes.sizeof(tray_manager.GUID), 16)
        self.assertEqual(ctypes.sizeof(tray_manager._UnionU), 4)
        # En Windows de 64 bits, NOTIFYICONDATAW mide exactamente 976 bytes
        is_64bit = sys.maxsize > 2**32
        if is_64bit:
            self.assertEqual(ctypes.sizeof(tray_manager.NOTIFYICONDATAW), 976)
        self.assertGreater(ctypes.sizeof(tray_manager.WNDCLASSEXW), 0)

    def test_tray_initialization(self):
        """Valida inicialización correcta de TrayManager con parámetros y límites de tooltip."""
        long_tooltip = "A" * 200
        tray = tray_manager.TrayManager(
            icon_path=self.icon_path,
            tooltip=long_tooltip,
            log_callback=self._log
        )
        self.assertEqual(len(tray.tooltip), 127, "El tooltip debe truncarse al límite de 128 chars")
        self.assertFalse(tray.is_running)
        self.assertFalse(tray.is_icon_added)

    def test_tray_lifecycle_start_and_stop(self):
        """Valida el inicio del hilo de mensajes y su detención limpia."""
        tray = tray_manager.TrayManager(
            icon_path=self.icon_path,
            tooltip="Test Lifecycle",
            log_callback=self._log
        )
        tray.start()
        time.sleep(0.15)
        self.assertTrue(tray.is_running, "El hilo de la bandeja debe reportar is_running=True")

        tray.stop()
        time.sleep(0.15)
        self.assertFalse(tray.is_running, "El hilo de la bandeja debe reportar is_running=False tras stop()")

    def test_callbacks_dispatch_in_threads(self):
        """Valida que los callbacks se ejecuten de forma asíncrona en hilos daemon."""
        events = []

        def sample_callback():
            events.append("called")

        tray = tray_manager.TrayManager(
            icon_path=self.icon_path,
            on_open_app=sample_callback,
            log_callback=self._log
        )
        tray._dispatch_callback(tray.on_open_app)
        time.sleep(0.1)
        self.assertIn("called", events)

    def test_show_balloon_defensive(self):
        """Valida que show_balloon maneje de forma segura entornos sin bandeja visible."""
        tray = tray_manager.TrayManager(
            icon_path=self.icon_path,
            log_callback=self._log
        )
        # Sin icono añadido, show_balloon debe retornar False sin lanzar excepción
        res = tray.show_balloon("Título", "Mensaje de prueba")
        self.assertFalse(res)

    def test_icon_fallback_when_file_missing(self):
        """Valida que un archivo de icono no existente no lance excepción y use fallback."""
        fake_icon = APP_DIR / "assets" / "non_existent_icon.ico"
        tray = tray_manager.TrayManager(
            icon_path=fake_icon,
            log_callback=self._log
        )
        hicon = tray._load_icon()
        self.assertIsNotNone(hicon)
        self.assertNotEqual(hicon, 0)
        # Limpieza
        tray_manager.user32.DestroyIcon(hicon)


    def test_tray_self_healing_reregisters_dropped_icon(self):
        """Valida que el temporizador de salud re-registre un icono descartado por Explorer."""
        tray = tray_manager.TrayManager(icon_path=self.icon_path, log_callback=self._log)
        # Sin ventana oculta, la verificación debe ser un no-op seguro
        tray._ensure_tray_icon()
        self.assertFalse(tray.is_icon_added)

        tray.start()
        time.sleep(0.3)
        try:
            if not tray.is_icon_added:
                self.skipTest("Bandeja de Windows no disponible en este entorno")
            # Simula que Explorer descartó el icono sin avisar
            tray_manager.shell32.Shell_NotifyIconW(
                tray_manager.NIM_DELETE, ctypes.byref(tray._create_notify_icon_data())
            )
            tray._ensure_tray_icon()
            self.assertTrue(tray.is_icon_added)
            self.assertTrue(any("Re-registrando" in m for m in self.log_messages))
        finally:
            tray.stop()


if __name__ == "__main__":
    unittest.main()
