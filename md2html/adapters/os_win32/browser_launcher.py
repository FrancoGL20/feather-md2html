#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loopback port allocator and Chromium (--app mode) window launcher adapter.
"""

import socket
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Callable, List, Optional

from md2html.adapters.os_win32.window_manager import (
    find_and_adjust_app_window,
    find_app_hwnds,
    get_dynamic_window_geometry,
)
from md2html.adapters.storage.logger import log_debug
from md2html.core.services.lifecycle_service import AppLifecycleState

DEFAULT_PORT = 51870

_EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
_CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_free_port() -> int:
    """Allocates an ephemeral free TCP port on loopback 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get_server_port(preferred_port: int = DEFAULT_PORT) -> int:
    """Attempts to bind preferred_port (51870) and falls back to an ephemeral free port if busy."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", preferred_port))
            return preferred_port
    except OSError:
        pass
    return find_free_port()


def launch_desktop_window(
    port: int,
    state: AppLifecycleState,
    adjust_window_fn: Optional[Callable] = None,
) -> None:
    """Launches Microsoft Edge or Google Chrome in native --app window mode."""
    url = f"http://127.0.0.1:{port}"
    target_w, target_h, pos_x, pos_y = get_dynamic_window_geometry()

    target_exe = None
    for cand in _EDGE_CANDIDATES + _CHROME_CANDIDATES:
        if Path(cand).exists():
            target_exe = cand
            break

    if target_exe:
        try:
            cmd = [
                target_exe,
                f"--app={url}",
                f"--window-size={target_w},{target_h}",
                f"--window-position={pos_x},{pos_y}",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ]
            log_debug(
                f"Iniciando ventana de app ({target_w}x{target_h} @ {pos_x},{pos_y}): {' '.join(cmd)}"
            )
            subprocess.Popen(cmd)

            adjust_cb = adjust_window_fn or (
                lambda tw, th, px, py: find_and_adjust_app_window(state, tw, th, px, py)
            )
            threading.Thread(
                target=adjust_cb,
                args=(target_w, target_h, pos_x, pos_y),
                daemon=True,
            ).start()
            return
        except Exception as e:
            log_debug(f"Aviso al lanzar modo app: {e}")

    log_debug(f"Abriendo navegador predeterminado: {url}")
    webbrowser.open(url)


def open_or_restore_app_window(
    state: AppLifecycleState,
    find_hwnds_fn: Callable[[], List[int]] = find_app_hwnds,
    launch_window_fn: Optional[Callable[[int], None]] = None,
) -> bool:
    """Restores and focuses the existing HWND if alive, or launches a new app window."""
    log_debug("open_app_window() invocado")
    launcher = launch_window_fn or (lambda p: launch_desktop_window(p, state))
    try:
        import ctypes

        user32 = ctypes.windll.user32
        SW_RESTORE = 9

        alive = [h for h in state.tracked_app_hwnds if user32.IsWindow(h)]
        if alive:
            for hwnd in alive:
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
            log_debug(f"Ventana existente restaurada y traída al frente (HWNDs: {alive})")
            return True

        found = find_hwnds_fn()
        if found:
            state.tracked_app_hwnds.update(found)
            for hwnd in found:
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
            log_debug(f"Ventanas descubiertas y traídas al frente: {found}")
            return True

        log_debug(
            f"No se detectó ventana viva. Relanzando ventana de escritorio en puerto {state.current_server_port}..."
        )
        launcher(state.current_server_port)
        return True
    except Exception as e:
        log_debug(f"Aviso en open_app_window: {e}")
        try:
            launcher(state.current_server_port)
        except Exception:
            pass
        return False
