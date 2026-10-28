#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Named Mutex adapter for single-instance application enforcement.
When a second process is launched, signals the active instance over loopback HTTP
to restore its window and exits cleanly.
"""

import urllib.request
from typing import Any

from md2html.adapters.storage.logger import log_debug

SINGLE_INSTANCE_MUTEX_NAME = "Local\\MarkdownToHTML_App_SingleInstance_Mutex"
DEFAULT_PORT = 51870


def acquire_single_instance_lock(
    mutex_name: str = SINGLE_INSTANCE_MUTEX_NAME,
    wake_port: int = DEFAULT_PORT,
) -> Any:
    """
    Acquires a Windows Named Mutex. If another instance already holds the lock,
    sends a wake request to the primary server and returns None.
    """
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        ERROR_ALREADY_EXISTS = 183

        mutex = kernel32.CreateMutexW(None, True, mutex_name)
        last_err = kernel32.GetLastError()
        if last_err == ERROR_ALREADY_EXISTS:
            log_debug("Instancia previa detectada mediante Named Mutex. Despertando app existente...")
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{wake_port}/api/open-app",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=1.5):
                    pass
            except Exception as e:
                log_debug(f"Aviso despertando instancia previa por HTTP: {e}")
            if mutex:
                kernel32.CloseHandle(mutex)
            return None
        return mutex
    except Exception as e:
        log_debug(f"Aviso en acquire_single_instance_lock: {e}")
        return None
