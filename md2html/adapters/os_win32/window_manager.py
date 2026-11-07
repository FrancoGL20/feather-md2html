#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Win32 window discovery, DPI-aware geometry calculation, and window positioning adapter.
"""

import time
from typing import Callable, List, Optional, Tuple

from md2html.adapters.storage.logger import log_debug
from md2html.core.services.lifecycle_service import AppLifecycleState


def find_app_hwnds() -> List[int]:
    """Enumerates active Windows top-level HWNDs matching the application title."""
    results: List[int] = []
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def enum_cb(hwnd: int, _lparam: int) -> bool:
            if user32.IsWindow(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    val = buff.value.strip()
                    if "Markdown to HTML" in val:
                        if "Visual Studio Code" not in val and "Sublime" not in val:
                            results.append(hwnd)
            return True

        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception as e:
        log_debug(f"Aviso en find_app_hwnds: {e}")
    return results


def is_app_window_alive(
    state: AppLifecycleState,
    find_hwnds_fn: Callable[[], List[int]] = find_app_hwnds,
) -> Optional[bool]:
    """
    Checks whether the native application window still exists in the OS.
    Returns True if alive, False if previously detected and now closed, or None if unknown.
    """
    try:
        import ctypes

        user32 = ctypes.windll.user32

        if state.tracked_app_hwnds:
            alive = {h for h in state.tracked_app_hwnds if user32.IsWindow(h)}
            state.tracked_app_hwnds = alive
            if state.tracked_app_hwnds:
                state.initial_window_detected = True
                return True

        found = find_hwnds_fn()
        if found:
            state.tracked_app_hwnds.update(found)
            state.initial_window_detected = True
            return True

        if state.initial_window_detected:
            return False
        return None
    except Exception:
        return None


def get_dynamic_window_geometry(
    screen_w: Optional[int] = None,
    screen_h: Optional[int] = None,
) -> Tuple[int, int, int, int]:
    """Calculates responsive window width, height, and centered coordinates based on display size."""
    if not screen_w or not screen_h:
        try:
            import ctypes

            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
            u = ctypes.windll.user32
            screen_w = u.GetSystemMetrics(0)
            screen_h = u.GetSystemMetrics(1)
        except Exception:
            screen_w = 1920
            screen_h = 1080

    try:
        screen_w = int(screen_w)
        screen_h = int(screen_h)
    except Exception:
        screen_w, screen_h = 1920, 1080

    if screen_w >= 1600:
        target_w = 750
        target_h = min(680, max(560, int(screen_h * 0.68)))
    else:
        target_w = max(680, min(1280, int(screen_w * 0.85)))
        target_h = max(560, min(760, int(screen_h * 0.86)))

    pos_x = max(0, (screen_w - target_w) // 2)
    pos_y = max(0, (screen_h - target_h) // 2)
    return target_w, target_h, pos_x, pos_y


def find_and_adjust_app_window(
    state: AppLifecycleState,
    target_w: int,
    target_h: int,
    pos_x: Optional[int] = None,
    pos_y: Optional[int] = None,
    retries: int = 25,
) -> bool:
    """Locates the Chromium app window and adjusts its native size and position via Win32 SetWindowPos."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        SW_RESTORE = 9
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        for _ in range(retries):
            found_hwnds: List[int] = []

            def enum_cb(hwnd: int, _lparam: int) -> bool:
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if "Markdown to HTML" in buff.value:
                            found_hwnds.append(hwnd)
                return True

            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

            if found_hwnds:
                state.tracked_app_hwnds.update(found_hwnds)
                state.initial_window_detected = True
                for hwnd in found_hwnds:
                    user32.ShowWindow(hwnd, SW_RESTORE)

                    rect = wintypes.RECT()
                    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                        curr_center_x = (rect.left + rect.right) // 2
                        curr_center_y = (rect.top + rect.bottom) // 2
                        final_x = max(0, curr_center_x - (target_w // 2))
                        final_y = max(0, curr_center_y - (target_h // 2))
                    else:
                        final_x = pos_x if pos_x is not None else 100
                        final_y = pos_y if pos_y is not None else 80

                    user32.SetWindowPos(
                        hwnd,
                        0,
                        final_x,
                        final_y,
                        target_w,
                        target_h,
                        SWP_NOZORDER | SWP_SHOWWINDOW,
                    )
                log_debug(f"Ventana ajustada nativamente a {target_w}x{target_h}")
                return True

            time.sleep(0.2)
    except Exception as e:
        log_debug(f"Aviso ajustando geometría de ventana: {e}")
    return False



def close_app_window(
    state: AppLifecycleState,
    find_hwnds_fn: Callable[[], List[int]] = find_app_hwnds,
) -> bool:
    """Closes the native Chromium app window by sending WM_CLOSE (equivalent to clicking 'X')."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        WM_CLOSE = 0x0010

        hwnds = list(state.tracked_app_hwnds) if state.tracked_app_hwnds else find_hwnds_fn()
        closed_any = False
        for hwnd in hwnds:
            if user32.IsWindow(hwnd):
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                closed_any = True
        if closed_any:
            log_debug(f"close_app_window: mensaje WM_CLOSE enviado a HWNDs={hwnds}")
        return closed_any
    except Exception as e:
        log_debug(f"Aviso al cerrar ventana de app: {e}")
        return False
