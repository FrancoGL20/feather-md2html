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

# Interval (seconds) between "server alive" diagnostic entries written by the watchdog.
WATCHDOG_ALIVE_LOG_INTERVAL = 600.0


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
        # True when the shutdown was explicitly requested by the user ("Salir completamente").
        # Such a shutdown can no longer be cancelled by client heartbeats or page reloads.
        self.force_shutdown: bool = False
        # True once the server was intentionally stopped (distinguishes it from unexpected exits).
        self.intentional_shutdown: bool = False

    def record_activity(self) -> None:
        """Records client HTTP activity and cancels any pending soft shutdown."""
        self.client_connected = True
        self.last_heartbeat = time.time()
        self.cancel_scheduled_shutdown(force=False)

    def schedule_shutdown(self, delay: float = 4.0, force: bool = False) -> None:
        """
        Schedules a deferred server shutdown to allow page reloads to cancel it.
        When `force` is True (explicit user quit) the shutdown is not cancellable by client activity.
        """
        self.shutdown_scheduled_time = time.time() + delay
        if force:
            self.force_shutdown = True
        log_debug(
            f"Apagado programado en {delay}s (forzado={force}, "
            f"timestamp objetivo: {self.shutdown_scheduled_time})"
        )

    def cancel_scheduled_shutdown(self, force: bool = True) -> None:
        """
        Cancels any scheduled shutdown.
        Client activity must call it with `force=False`, which never cancels an explicit user quit.
        Administrative callers use the default `force=True`.
        """
        if self.force_shutdown and not force:
            return
        if force:
            self.force_shutdown = False
        if self.shutdown_scheduled_time is not None:
            log_debug("Apagado programado CANCELADO por actividad de cliente o presencia de ventana.")
            self.shutdown_scheduled_time = None


def _shutdown_server(server: HTTPServer, state: AppLifecycleState) -> None:
    """Marks the shutdown as intentional and stops the HTTP server loop."""
    state.intentional_shutdown = True
    server.shutdown()


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
            try:
                cfg = get_config_fn()
            except Exception:
                cfg = {}
            tray_active = bool(
                state.tray_instance and getattr(state.tray_instance, "is_running", False)
            )
            if (
                cfg.get("system_tray_enabled", True)
                and cfg.get("close_to_tray", True)
                and tray_active
            ):
                log_debug(
                    "Sin conexión web inicial en 120s, pero el System Tray está activo. "
                    "Preservando servidor e iniciando supervisión en segundo plano."
                )
                break
            log_debug("No se detectó conexión inicial en 120s ni bandeja activa. Apagando servidor.")
            _shutdown_server(server, state)
            return

    log_debug("Watchdog: Frontend conectado con éxito. Iniciando supervisión activa.")
    last_alive_log = time.time()

    while True:
        time.sleep(2)
        now = time.time()

        # Explicit user quit: never cancellable and independent of heartbeat freshness.
        if state.force_shutdown and state.shutdown_scheduled_time is not None:
            if now >= state.shutdown_scheduled_time:
                log_debug("Apagado ordenado ejecutado tras solicitud explícita de salida.")
                _shutdown_server(server, state)
                break
            continue

        if now - last_alive_log >= WATCHDOG_ALIVE_LOG_INTERVAL:
            last_alive_log = now
            log_debug(
                f"Watchdog: servidor activo (último latido hace {int(now - state.last_heartbeat)}s, "
                f"HWNDs rastreados={len(state.tracked_app_hwnds)})."
            )

        if now - state.last_heartbeat < 10:
            state.cancel_scheduled_shutdown(force=False)
            continue

        if state.shutdown_scheduled_time is not None:
            if now >= state.shutdown_scheduled_time:
                log_debug("Apagado ordenado ejecutado tras recibir señal de cierre.")
                _shutdown_server(server, state)
                break
            continue

        if now - state.last_heartbeat > 180:
            try:
                window_status = is_window_alive_fn()
            except Exception as e:
                log_debug(f"Aviso comprobando ventana nativa en watchdog: {e}")
                window_status = None
            if window_status is True:
                state.last_heartbeat = now
                continue

            try:
                cfg = get_config_fn()
            except Exception as e:
                # Never let a transient config/disk error take the whole app down.
                log_debug(f"Aviso leyendo configuración en watchdog (se preserva servidor): {e}")
                continue
            tray_active = bool(
                state.tray_instance and getattr(state.tray_instance, "is_running", False)
            )
            if (
                cfg.get("system_tray_enabled", True)
                and cfg.get("close_to_tray", True)
                and tray_active
            ):
                continue
            log_debug("Inactividad prolongada sin latidos ni ventana abierta (180s). Apagando servidor...")
            _shutdown_server(server, state)
            break
