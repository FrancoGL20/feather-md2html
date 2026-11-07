#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML — Desktop Application Entrypoint.
Composes the Hexagonal Architecture adapters (`md2html.adapters`) and core
services (`md2html.core.services`) to run the local HTTP server, native Chromium
window, and Windows System Tray controller.
"""

import atexit
from datetime import datetime
import faulthandler
from http.server import HTTPServer, ThreadingHTTPServer
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import types
from typing import Any, Dict, List, Optional
import webbrowser

# Configure stdout for UTF-8 on Windows (safe for pythonw where stdout is None)
if sys.stdout and getattr(sys.stdout, "encoding", None):
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure that if app.py is run directly as __main__, any subsequent 'import app'
# resolves to the exact same module object and lifecycle state.
if __name__ == "__main__":
    sys.modules["app"] = sys.modules["__main__"]

from md2html.adapters.http import AppRequestHandler
from md2html.adapters.os_win32 import (
    DEFAULT_PORT,
    SINGLE_INSTANCE_MUTEX_NAME,
    TrayManager,
    acquire_single_instance_lock as _acquire_mutex,
    choose_file_native,
    choose_folder_native,
    close_app_window as _close_hwnd,
    find_and_adjust_app_window as _adjust_hwnd,
    find_app_hwnds,
    find_free_port,
    get_clipboard_text,
    get_dynamic_window_geometry,
    get_server_port,
    is_app_window_alive as _check_hwnd_alive,
    launch_desktop_window as _launch_chromium,
    open_or_restore_app_window,
)
from md2html.adapters.storage import (
    JsonConfigRepository,
    extract_title_from_html,
    log_debug,
)
from md2html.core.services import (
    AppLifecycleState,
    generate_index_html,
    run_watchdog_loop,
)

APP_DIR = Path(__file__).resolve().parent
UI_DIR = APP_DIR / "ui"
ASSETS_DIR = APP_DIR / "assets"
CONFIG_FILE = APP_DIR / "config.json"
CONFIG_TEMPLATE_FILE = APP_DIR / "config.template.json"
DEFAULT_ROOT_DIR = Path.home() / "Downloads" / "Markdown_HTML_Library"

# Encapsulated application lifecycle state and configuration repository
_lifecycle = AppLifecycleState(default_port=DEFAULT_PORT)

_config_repo = JsonConfigRepository(
    config_file_getter=lambda: CONFIG_FILE,
    template_file_getter=lambda: CONFIG_TEMPLATE_FILE,
    default_root_getter=lambda: DEFAULT_ROOT_DIR,
    index_generator=generate_index_html,
)


def get_or_create_config() -> Dict[str, Any]:
    """Loads or initializes config.json and synchronizes physical library history."""
    return _config_repo.get_or_create_config()


def save_config(config: Dict[str, Any]) -> None:
    """Persists configuration dictionary to CONFIG_FILE."""
    _config_repo.save_config(config)


def add_recent_conversion(doc_info: Dict[str, Any]) -> None:
    """Adds a converted document entry to recent_conversions history."""
    _config_repo.add_recent_conversion(doc_info)


def schedule_shutdown(delay: float = 4.0, force: bool = False) -> None:
    """Schedules a deferred server shutdown."""
    _lifecycle.schedule_shutdown(delay=delay, force=force)


def cancel_scheduled_shutdown(force: bool = True) -> None:
    """Cancels any pending scheduled server shutdown."""
    _lifecycle.cancel_scheduled_shutdown(force=force)


def acquire_single_instance_lock() -> Any:
    """Acquires the Windows Named Mutex or wakes the existing application instance."""
    return _acquire_mutex(SINGLE_INSTANCE_MUTEX_NAME, DEFAULT_PORT)


def close_app_window() -> bool:
    """Closes the active application window while preserving the tray and background server."""
    return _close_hwnd(_lifecycle, find_hwnds_fn=find_app_hwnds)


def is_app_window_alive() -> Optional[bool]:
    """Checks whether the native application window exists in the OS."""
    return _check_hwnd_alive(_lifecycle, find_hwnds_fn=find_app_hwnds)


def find_and_adjust_app_window(
    target_w: int,
    target_h: int,
    pos_x: Optional[int] = None,
    pos_y: Optional[int] = None,
    retries: int = 25,
) -> bool:
    """Finds the active application HWND and adjusts its geometry."""
    return _adjust_hwnd(_lifecycle, target_w, target_h, pos_x, pos_y, retries=retries)


def launch_desktop_window(port: int) -> None:
    """Launches the Chromium --app window pointed at the local loopback server."""
    _launch_chromium(port, _lifecycle, adjust_window_fn=find_and_adjust_app_window)


def open_app_window() -> bool:
    """Restores the existing application window or launches a new one."""
    return open_or_restore_app_window(
        _lifecycle,
        find_hwnds_fn=find_app_hwnds,
        launch_window_fn=launch_desktop_window,
    )


def open_documents_folder() -> None:
    """Opens the configured library root directory in Windows Explorer."""
    cfg = get_or_create_config()
    r_dir = cfg.get("root_dir", "")
    if r_dir and Path(r_dir).exists():
        try:
            os.startfile(r_dir)
        except Exception as e:
            log_debug(f"Error abriendo carpeta desde tray: {e}")


def open_library_index() -> None:
    """Opens the library catalog index.html in the default system browser."""
    cfg = get_or_create_config()
    idx_file = Path(cfg.get("root_dir", "")) / "index.html"
    if idx_file.exists():
        webbrowser.open(f"file:///{idx_file.resolve().as_posix()}")
    else:
        open_documents_folder()


def quit_app_fully() -> None:
    """Stops the system tray controller and schedules an immediate server shutdown."""
    log_debug("quit_app_fully() invocado: cerrando tray y finalizando servidor...")
    if _lifecycle.tray_instance:
        try:
            _lifecycle.tray_instance.stop()
        except Exception as e:
            log_debug(f"Aviso deteniendo tray en quit_app_fully: {e}")
    schedule_shutdown(0.1, force=True)


def watchdog_thread(server: HTTPServer) -> None:
    """Runs the background lifecycle watchdog loop for the given HTTPServer."""
    run_watchdog_loop(
        server=server,
        state=_lifecycle,
        is_window_alive_fn=is_app_window_alive,
        get_config_fn=get_or_create_config,
    )


def _install_diagnostics() -> None:
    """
    Installs process-level diagnostics so that silent deaths of the windowless
    `pythonw.exe` process leave a trace (native crashes, uncaught thread errors, exit).
    """
    try:
        fault_file = open(APP_DIR / "crash_native.txt", "a", buffering=1, encoding="utf-8")
        faulthandler.enable(file=fault_file, all_threads=True)
        _lifecycle.fault_log_file = fault_file
    except Exception as e:
        log_debug(f"Aviso activando faulthandler: {e}")

    def _thread_hook(args: Any) -> None:
        log_debug(
            f"Excepción no controlada en hilo '{getattr(args.thread, 'name', '?')}': "
            f"{''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))}"
        )

    threading.excepthook = _thread_hook
    atexit.register(
        lambda: log_debug(
            f"Proceso finalizando (apagado intencional={_lifecycle.intentional_shutdown})."
        )
    )


def main() -> None:
    """Application entrypoint: acquires lock, starts HTTP server, tray, and UI window."""
    log_debug("--- Inicio de main() ---")
    _install_diagnostics()

    _lifecycle.app_single_instance_mutex = acquire_single_instance_lock()
    if _lifecycle.app_single_instance_mutex is None:
        log_debug("Proceso secundario finalizado: instancia primaria ya activa.")
        sys.exit(0)

    cfg = get_or_create_config()
    log_debug("Configuración obtenida/creada")
    port = get_server_port()
    _lifecycle.current_server_port = port
    log_debug(f"Puerto asignado: {port}")
    _lifecycle.record_activity()
    _lifecycle.client_connected = False

    AppRequestHandler.runtime_facade = sys.modules[__name__]
    server = ThreadingHTTPServer(("127.0.0.1", port), AppRequestHandler)
    _lifecycle.server_instance = server
    log_debug("ThreadingHTTPServer instanciado")

    t_watchdog = threading.Thread(target=watchdog_thread, args=(server,), daemon=True)
    t_watchdog.start()
    log_debug("Watchdog iniciado en hilo daemon")

    if cfg.get("system_tray_enabled", True):
        try:
            icon_path = ASSETS_DIR / "app_icon.ico"
            _lifecycle.tray_instance = TrayManager(
                icon_path=icon_path,
                tooltip="Markdown to HTML — Desktop App",
                on_open_app=open_app_window,
                on_open_folder=open_documents_folder,
                on_open_index=open_library_index,
                on_quit=quit_app_fully,
                log_callback=log_debug,
            )
            _lifecycle.tray_instance.start()
            log_debug("TrayManager iniciado en hilo daemon")
        except Exception as e:
            log_debug(f"Aviso al iniciar TrayManager: {e}")

    log_debug(f"Llamando a launch_desktop_window({port})...")
    launch_desktop_window(port)
    log_debug("launch_desktop_window completado")

    log_debug("Entrando a server.serve_forever()...")
    try:
        while True:
            try:
                server.serve_forever()
                log_debug("server.serve_forever() terminó de forma natural")
            except Exception as e:
                log_debug(f"Excepción en serve_forever: {e}\n{traceback.format_exc()}")
            if _lifecycle.intentional_shutdown:
                break
            # Salida inesperada del bucle HTTP: se reanuda para que la app no quede "sorda"
            log_debug("serve_forever() terminó SIN apagado intencional. Reanudando servidor...")
            time.sleep(0.5)
    finally:
        log_debug("Bloque finally de main(): cerrando servidor y tray")
        if _lifecycle.tray_instance:
            try:
                _lifecycle.tray_instance.stop()
            except Exception:
                pass
        if _lifecycle.app_single_instance_mutex:
            try:
                import ctypes

                ctypes.windll.kernel32.CloseHandle(_lifecycle.app_single_instance_mutex)
            except Exception:
                pass
        server.server_close()


class _AppModuleProxy(types.ModuleType):
    """
    Module-level property proxy bridging legacy attribute access (e.g. in tests)
    directly to the encapsulated `AppLifecycleState` instance (`_lifecycle`).
    """

    _STATE_FIELDS = frozenset(
        {
            "last_heartbeat",
            "server_instance",
            "client_connected",
            "tracked_app_hwnds",
            "shutdown_scheduled_time",
            "initial_window_detected",
            "tray_instance",
            "current_server_port",
            "app_single_instance_mutex",
        }
    )

    def __getattr__(self, name: str) -> Any:
        if name in self._STATE_FIELDS:
            return getattr(_lifecycle, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._STATE_FIELDS:
            setattr(_lifecycle, name, value)
        else:
            super().__setattr__(name, value)


sys.modules[__name__].__class__ = _AppModuleProxy

if __name__ == "__main__":
    try:
        main()
    except Exception:
        crash_file = APP_DIR / "crash_log.txt"
        with open(crash_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- CRASH {datetime.now()} ---\n")
            f.write(traceback.format_exc())
