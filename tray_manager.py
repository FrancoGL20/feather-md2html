#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML — System Tray Manager (Bandeja del Sistema)
Módulo nativo ultraligero para integración en el área de notificación de Windows.
Cero dependencias externas. Totalmente autónomo y portable (Win32 ctypes).
"""

import sys
import time
import ctypes
from ctypes import wintypes
import threading
from pathlib import Path

# Configurar tipos y funciones nativas de Win32
user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32

# Constantes Win32
WM_NULL = 0x0000
WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_USER = 0x0400
WM_TRAY_CALLBACK = WM_USER + 20

WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010

NIIF_NONE = 0x00000000
NIIF_INFO = 0x00000001
NIIF_WARNING = 0x00000002
NIIF_ERROR = 0x00000003

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

TPM_LEFTALIGN = 0x0000
TPM_BOTTOMALIGN = 0x0020
TPM_RIGHTBUTTON = 0x0002

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MF_BYCOMMAND = 0x00000000
MF_DEFAULT = 0x00001000

# IDs de menú contextual
ID_MENU_OPEN_APP = 1001
ID_MENU_OPEN_FOLDER = 1002
ID_MENU_OPEN_INDEX = 1003
ID_MENU_QUIT = 1004

# Estructuras ctypes para Win32
class GUID(ctypes.Structure):
    _fields_ = (
        ("Data1", wintypes.ULONG),
        ("Data2", wintypes.USHORT),
        ("Data3", wintypes.USHORT),
        ("Data4", wintypes.BYTE * 8),
    )

class _UnionU(ctypes.Union):
    _fields_ = (
        ("uTimeout", wintypes.UINT),
        ("uVersion", wintypes.UINT),
    )

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = (
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("u", _UnionU),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    )

WNDPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]

# Configuración de firmas de API
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetLastError.restype = wintypes.DWORD

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = wintypes.LPARAM

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype = None

user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

user32.CreatePopupMenu.argtypes = []
user32.CreatePopupMenu.restype = wintypes.HMENU

user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_uint64, wintypes.LPCWSTR]
user32.AppendMenuW.restype = wintypes.BOOL

user32.SetMenuDefaultItem.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
user32.SetMenuDefaultItem.restype = wintypes.BOOL

user32.TrackPopupMenuEx.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.HWND, ctypes.c_void_p]
user32.TrackPopupMenuEx.restype = wintypes.BOOL

user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.DestroyMenu.restype = wintypes.BOOL

user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.LoadImageW.restype = wintypes.HICON

user32.DestroyIcon.argtypes = [wintypes.HICON]
user32.DestroyIcon.restype = wintypes.BOOL

user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
user32.RegisterWindowMessageW.restype = wintypes.UINT

shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL


class TrayManager:
    """
    Controlador nativo del icono en la bandeja del sistema (System Tray) para Windows.
    Gestiona el ciclo de vida del icono, menú contextual y eventos de usuario.
    """

    def __init__(
        self,
        icon_path: Path = None,
        tooltip: str = "Markdown to HTML — Desktop App",
        on_open_app=None,
        on_open_folder=None,
        on_open_index=None,
        on_quit=None,
        log_callback=None
    ):
        self.icon_path = Path(icon_path) if icon_path else None
        self.tooltip = tooltip[:127]  # Límite de 128 caracteres en szTip
        self.on_open_app = on_open_app
        self.on_open_folder = on_open_folder
        self.on_open_index = on_open_index
        self.on_quit = on_quit
        self.log_callback = log_callback or (lambda msg: None)

        self.hwnd = None
        self.hicon = None
        self.hinst = None
        self.class_name = f"MarkdownToHTML_TrayWindow_{id(self)}"
        self.wm_taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")

        self._thread = None
        self._is_running = False
        self._is_icon_added = False
        self._wndproc_cb = WNDPROC(self._window_proc)
        self._lock = threading.Lock()

    def _log(self, msg: str):
        try:
            self.log_callback(f"[TrayManager] {msg}")
        except Exception:
            pass

    def _load_icon(self) -> wintypes.HICON:
        if self.icon_path and self.icon_path.is_file():
            try:
                # Obtener tamaño de icono pequeño del sistema (generalmente 16x16)
                cx = user32.GetSystemMetrics(49) or 16  # SM_CXSMICON = 49
                cy = user32.GetSystemMetrics(50) or 16  # SM_CYSMICON = 50
                hicon = user32.LoadImageW(
                    None,
                    str(self.icon_path.resolve()),
                    IMAGE_ICON,
                    cx,
                    cy,
                    LR_LOADFROMFILE
                )
                if hicon:
                    return hicon
            except Exception as e:
                self._log(f"Aviso cargando icono desde archivo: {e}")

        # Fallback a icono de aplicación por defecto de Windows
        IDI_APPLICATION = 32512
        return user32.LoadIconW(None, wintypes.LPCWSTR(IDI_APPLICATION))

    def _create_notify_icon_data(self, flags=NIF_MESSAGE | NIF_ICON | NIF_TIP) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = flags
        nid.uCallbackMessage = WM_TRAY_CALLBACK
        nid.hIcon = self.hicon
        nid.szTip = self.tooltip
        return nid

    def _add_tray_icon(self) -> bool:
        if not self.hwnd or not self.hicon:
            return False
        nid = self._create_notify_icon_data()
        res = shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        if res:
            self._is_icon_added = True
            self._log("Icono añadido con éxito a la bandeja del sistema.")
            return True
        else:
            err = kernel32.GetLastError()
            self._log(f"Aviso: Shell_NotifyIconW NIM_ADD retornó 0 (GetLastError={err}). Modo degradado sin bandeja.")
            return False

    def _remove_tray_icon(self):
        if self._is_icon_added and self.hwnd:
            nid = self._create_notify_icon_data()
            try:
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                self._log("Icono eliminado de la bandeja del sistema.")
            except Exception as e:
                self._log(f"Error eliminando icono del tray: {e}")
            finally:
                self._is_icon_added = False

    def show_balloon(self, title: str, message: str, timeout_ms: int = 3500) -> bool:
        """Muestra una burbuja/notificación nativa de Windows en el icono de la bandeja."""
        if not self._is_icon_added or not self.hwnd:
            return False
        try:
            nid = self._create_notify_icon_data(flags=NIF_INFO)
            nid.szInfoTitle = title[:63]
            nid.szInfo = message[:255]
            nid.dwInfoFlags = NIIF_INFO
            nid.u.uTimeout = timeout_ms
            res = shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
            self._log(f"Notificación en globo enviada ({title}): resultado={res}")
            return bool(res)
        except Exception as e:
            self._log(f"Error mostrando notificación en globo: {e}")
            return False

    def _show_context_menu(self):
        """Construye y despliega el menú contextual nativo en la posición del cursor."""
        if not self.hwnd:
            return

        hmenu = user32.CreatePopupMenu()
        if not hmenu:
            return

        try:
            # Opción 1: Abrir aplicación (por defecto / negrita)
            user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_OPEN_APP, "📌 Abrir Markdown to HTML")
            user32.SetMenuDefaultItem(hmenu, ID_MENU_OPEN_APP, MF_BYCOMMAND)

            # Opción 2: Abrir carpeta de documentos
            user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_OPEN_FOLDER, "📂 Abrir Carpeta de Documentos")

            # Opción 3: Ver biblioteca index.html
            user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_OPEN_INDEX, "📚 Ver Biblioteca (index.html)")

            # Separador
            user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)

            # Opción 4: Salir
            user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_QUIT, "❌ Salir completamente")

            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))

            # Requisito de la API Win32: SetForegroundWindow antes de TrackPopupMenuEx
            user32.SetForegroundWindow(self.hwnd)
            user32.TrackPopupMenuEx(hmenu, TPM_BOTTOMALIGN | TPM_LEFTALIGN | TPM_RIGHTBUTTON, pt.x, pt.y, self.hwnd, None)
            # Requisito de la API Win32: PostMessage WM_NULL para cerrar el menú si se hace clic fuera
            user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        finally:
            user32.DestroyMenu(hmenu)

    def _dispatch_callback(self, cb):
        if callable(cb):
            threading.Thread(target=cb, daemon=True).start()

    def _window_proc(self, hwnd, msg, wparam, lparam):
        # Evento del icono de la bandeja
        if msg == WM_TRAY_CALLBACK:
            if lparam in (WM_LBUTTONUP, WM_LBUTTONDBLCLK):
                self._dispatch_callback(self.on_open_app)
                return 0
            elif lparam == WM_RBUTTONUP:
                self._show_context_menu()
                return 0

        # Comandos del menú contextual
        elif msg == WM_COMMAND:
            cmd_id = wintypes.LOWORD(wparam) if hasattr(wintypes, 'LOWORD') else (wparam & 0xFFFF)
            if cmd_id == ID_MENU_OPEN_APP:
                self._dispatch_callback(self.on_open_app)
                return 0
            elif cmd_id == ID_MENU_OPEN_FOLDER:
                self._dispatch_callback(self.on_open_folder)
                return 0
            elif cmd_id == ID_MENU_OPEN_INDEX:
                self._dispatch_callback(self.on_open_index)
                return 0
            elif cmd_id == ID_MENU_QUIT:
                self._dispatch_callback(self.on_quit)
                return 0

        # Recuperación automática si Explorer se reinicia
        elif msg != 0 and msg == self.wm_taskbar_created:
            self._log("Señal TaskbarCreated recibida de Explorer. Re-registrando icono...")
            self._add_tray_icon()
            return 0

        elif msg == WM_DESTROY:
            self._remove_tray_icon()
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _run_loop(self):
        """Bucle de mensajes Win32 ejecutándose en hilo dedicado."""
        self._log("Iniciando bucle de mensajes Win32 para System Tray...")
        self.hinst = kernel32.GetModuleHandleW(None)

        # Registrar clase de ventana
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc_cb
        wc.hInstance = self.hinst
        wc.lpszClassName = self.class_name

        atom = user32.RegisterClassExW(ctypes.byref(wc))
        if not atom:
            err = kernel32.GetLastError()
            self._log(f"Error registrando clase de ventana para tray: {err}")
            self._is_running = False
            return

        # Crear ventana oculta
        WS_OVERLAPPED = 0x00000000
        self.hwnd = user32.CreateWindowExW(
            0, self.class_name, "MarkdownToHTML_TrayHiddenWindow", WS_OVERLAPPED,
            0, 0, 0, 0, None, None, self.hinst, None
        )

        if not self.hwnd:
            err = kernel32.GetLastError()
            self._log(f"Error creando ventana oculta para tray: {err}")
            user32.UnregisterClassW(self.class_name, self.hinst)
            self._is_running = False
            return

        # Cargar icono
        self.hicon = self._load_icon()

        # Añadir al System Tray
        self._add_tray_icon()
        self._is_running = True

        # Bucle de despacho de mensajes
        msg = wintypes.MSG()
        while self._is_running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        self._log("Bucle de mensajes Win32 finalizado.")
        # Limpieza de recursos
        self._remove_tray_icon()
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
        if self.class_name and self.hinst:
            user32.UnregisterClassW(self.class_name, self.hinst)
        if self.hicon:
            user32.DestroyIcon(self.hicon)
            self.hicon = None
        self._is_running = False

    def start(self):
        """Inicia el administrador del System Tray en un hilo daemon secundario."""
        with self._lock:
            if self._is_running or (self._thread and self._thread.is_alive()):
                return
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="SystemTrayThread")
            self._thread.start()
            # Breve pausa para permitir inicialización
            time.sleep(0.08)

    def stop(self):
        """Detiene el administrador del System Tray y remueve el icono."""
        with self._lock:
            self._is_running = False
            if self.hwnd:
                user32.PostMessageW(self.hwnd, WM_DESTROY, 0, 0)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
            self._remove_tray_icon()

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_icon_added(self) -> bool:
        return self._is_icon_added
