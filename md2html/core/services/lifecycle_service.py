#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application lifecycle state and watchdog supervision service.
Encapsulates server heartbeat tracking, native HWND window tracking,
graceful shutdown scheduling, and background watchdog monitoring without loose globals.
"""

import time
from http.server import HTTPServer
from typing import Any, Callable, Dict, Optional, Set

from md2html.adapters.storage.logger import log_debug


class AppLifecycleState:
    """Encapsulates runtime state for the desktop application server."""

    def __init__(self, default_port: int = 51870) -> None:
        self.last_heartbeat: float = time.time()
        self.server_instance: Optional[HTTPServer] = None
        self.client_connected: bool = False
        self.tracked_app_hwnds: Set[int] = set()
        self.shutdown_scheduled_time: Optional[float] = None
        self.initial_window_detected: bool = False
        self.tray_instance: Any = None
        self.current_server_port: int = default_port
        self.app_single_instance_mutex: Any = None

    def record_activity(self) -> None:
        """Records client HTTP activity and cancels any pending shutdown."""
        self.client_connected = True
        self.last_heartbeat = time.time()
        self.cancel_scheduled_shutdown()

    def schedule_shutdown(self, delay: float = 4.0) -> None:
        """Schedules a deferred server shutdown to allow page reloads to cancel it."""
        self.shutdown_scheduled_time = time.time() + delay
        log_debug(
            f"Apagado programado en {delay}s (timestamp objetivo: {self.shutdown_scheduled_time})"
        )

    def cancel_scheduled_shutdown(self) -> None:
        """Cancels any scheduled shutdown when valid client activity is detected."""
        if self.shutdown_scheduled_time is not None:
            log_debug("Apagado programado CANCELADO por actividad de cliente o presencia de ventana.")
            self.shutdown_scheduled_time = None


def run_watchdog_loop(
    server: HTTPServer,
    state: AppLifecycleState,
    is_window_alive_fn: Callable[[], Optional[bool]],
    get_config_fn: Callable[[], Dict[str, Any]],
) -> None:
    """
    Monitors client heartbeats and native Windows HWND handles.
    Keeps the server alive indefinitely while the window or system tray is active,
    and shuts down cleanly when the window is closed and tray mode is disabled.
    """
    start_time = time.time()

    while not state.client_connected:
        time.sleep(1)
        if time.time() - start_time > 120:
            log_debug("No se detectó conexión inicial en 120s. Apagando servidor.")
            server.shutdown()
            return

    log_debug("Watchdog: Frontend conectado con éxito. Iniciando supervisión activa.")

    while True:
        time.sleep(2)
        now = time.time()

        if now - state.last_heartbeat < 10:
            state.cancel_scheduled_shutdown()
            continue

        if state.shutdown_scheduled_time is not None:
            if now >= state.shutdown_scheduled_time:
                log_debug("Apagado ordenado ejecutado tras recibir señal de cierre.")
                server.shutdown()
                break
            continue

        if now - state.last_heartbeat > 180:
            window_status = is_window_alive_fn()
            if window_status is True:
                state.last_heartbeat = now
                continue
            else:
                cfg = get_config_fn()
                if cfg.get("system_tray_enabled", True) and cfg.get("close_to_tray", True):
                    time.sleep(2)
                    continue
                log_debug("Inactividad prolongada sin latidos ni ventana abierta (180s). Apagando servidor...")
                server.shutdown()
                break
