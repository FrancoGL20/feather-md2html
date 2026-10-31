#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Native Win32 clipboard adapter using user32/kernel32 ctypes.
Reads CF_UNICODETEXT directly from OS memory without browser permission prompts.
"""

import time

from md2html.adapters.storage.logger import log_debug


def get_clipboard_text() -> str:
    """Reads Unicode text from the Windows clipboard via Win32 API."""
    try:
        import ctypes
        from ctypes import wintypes

        u32 = ctypes.windll.user32
        k32 = ctypes.windll.kernel32

        u32.OpenClipboard.argtypes = [wintypes.HWND]
        u32.OpenClipboard.restype = wintypes.BOOL
        u32.GetClipboardData.argtypes = [wintypes.UINT]
        u32.GetClipboardData.restype = wintypes.HANDLE
        u32.CloseClipboard.argtypes = []
        u32.CloseClipboard.restype = wintypes.BOOL

        k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalLock.restype = ctypes.c_void_p
        k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalUnlock.restype = wintypes.BOOL

        CF_UNICODETEXT = 13

        for _ in range(5):
            if u32.OpenClipboard(None):
                break
            time.sleep(0.05)
        else:
            return ""

        try:
            handle = u32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            ptr = k32.GlobalLock(handle)
            if not ptr:
                return ""
            try:
                return ctypes.c_wchar_p(ptr).value or ""
            finally:
                k32.GlobalUnlock(handle)
        finally:
            u32.CloseClipboard()
    except Exception as e:
        log_debug(f"Aviso al leer portapapeles nativo: {e}")
        return ""
