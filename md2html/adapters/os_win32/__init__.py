#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows OS native adapters (Win32 ctypes, single-instance mutex, clipboard, tray, and dialogs)."""

from md2html.adapters.os_win32.browser_launcher import (
    DEFAULT_PORT,
    find_free_port,
    get_server_port,
    launch_desktop_window,
    open_or_restore_app_window,
)
from md2html.adapters.os_win32.clipboard import get_clipboard_text
from md2html.adapters.os_win32.dialogs import (
    choose_file_native,
    choose_folder_native,
)
from md2html.adapters.os_win32.mutex import (
    SINGLE_INSTANCE_MUTEX_NAME,
    acquire_single_instance_lock,
)
from md2html.adapters.os_win32.system_tray import (
    GUID,
    NOTIFYICONDATAW,
    TrayManager,
    WNDCLASSEXW,
    _UnionU,
)
from md2html.adapters.os_win32.window_manager import (
    find_and_adjust_app_window,
    find_app_hwnds,
    get_dynamic_window_geometry,
    is_app_window_alive,
)

__all__ = [
    "DEFAULT_PORT",
    "GUID",
    "NOTIFYICONDATAW",
    "SINGLE_INSTANCE_MUTEX_NAME",
    "TrayManager",
    "WNDCLASSEXW",
    "_UnionU",
    "acquire_single_instance_lock",
    "choose_file_native",
    "choose_folder_native",
    "find_and_adjust_app_window",
    "find_app_hwnds",
    "find_free_port",
    "get_clipboard_text",
    "get_dynamic_window_geometry",
    "get_server_port",
    "is_app_window_alive",
    "launch_desktop_window",
    "open_or_restore_app_window",
]
