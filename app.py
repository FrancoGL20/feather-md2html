#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML — Desktop Application Server
Servidor local ultraligero y silencioso que orquesta la aplicación en modo ventana nativa.
Cero dependencias externas. Totalmente portable.
"""

import os
import sys
import re
import json
import time
import socket
import threading
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configure stdout for UTF-8 on Windows (safe for pythonw where stdout is None)
if sys.stdout and getattr(sys.stdout, 'encoding', None):
    try:
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Importar motor de compilación
import md_engine
import tray_manager

APP_DIR = Path(__file__).resolve().parent
UI_DIR = APP_DIR / "ui"
ASSETS_DIR = APP_DIR / "assets"
CONFIG_FILE = APP_DIR / "config.json"
CONFIG_TEMPLATE_FILE = APP_DIR / "config.template.json"

DEFAULT_ROOT_DIR = Path.home() / "Downloads" / "Markdown_HTML_Library"
DEFAULT_PORT = 51870

# Estado global de supervisión y ciclo de vida
last_heartbeat = time.time()
server_instance = None
client_connected = False
tracked_app_hwnds = set()
shutdown_scheduled_time = None
initial_window_detected = False
tray_instance = None
current_server_port = DEFAULT_PORT
app_single_instance_mutex = None
SINGLE_INSTANCE_MUTEX_NAME = "Local\\MarkdownToHTML_App_SingleInstance_Mutex"

def acquire_single_instance_lock():
    """
    Verifica si ya existe otra instancia de la aplicación ejecutándose en Windows.
    Si ya existe, solicita a la instancia existente que despierte y traiga al frente su ventana visual,
    y retorna None para que el proceso duplicado termine inmediatamente sin crear iconos extras.
    """
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        ERROR_ALREADY_EXISTS = 183

        mutex = kernel32.CreateMutexW(None, True, SINGLE_INSTANCE_MUTEX_NAME)
        last_err = kernel32.GetLastError()
        if last_err == ERROR_ALREADY_EXISTS:
            log_debug("Instancia previa detectada mediante Named Mutex. Despertando app existente...")
            # Notificar a la instancia existente para que abra o restaure la ventana
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://127.0.0.1:{DEFAULT_PORT}/api/open-app",
                    data=b"{}",
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=1.5) as response:
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

def open_app_window():
    """
    Restaura y trae al frente la ventana de la app si ya existe en el SO,
    o lanza una nueva instancia de la ventana contra el servidor existente.
    """
    global current_server_port, tracked_app_hwnds
    log_debug("open_app_window() invocado")
    try:
        import ctypes
        user32 = ctypes.windll.user32
        SW_RESTORE = 9

        # 1. Comprobar HWNDs previamente rastreados
        alive = [h for h in tracked_app_hwnds if user32.IsWindow(h)]
        if alive:
            for hwnd in alive:
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
            log_debug(f"Ventana existente restaurada y traída al frente (HWNDs: {alive})")
            return True

        # 2. Descubrir ventanas activas en el SO
        found = find_app_hwnds()
        if found:
            tracked_app_hwnds.update(found)
            for hwnd in found:
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
            log_debug(f"Ventanas descubiertas y traídas al frente: {found}")
            return True

        # 3. Si no existe ventana abierta de Edge, volver a lanzarla contra el servidor existente
        log_debug(f"No se detectó ventana viva. Relanzando ventana de escritorio en puerto {current_server_port}...")
        launch_desktop_window(current_server_port)
        return True
    except Exception as e:
        log_debug(f"Aviso en open_app_window: {e}")
        try:
            launch_desktop_window(current_server_port)
        except Exception:
            pass
        return False

def open_documents_folder():
    """Abre la carpeta raíz de documentos en el Explorador de Windows."""
    cfg = get_or_create_config()
    r_dir = cfg.get("root_dir", "")
    if r_dir and Path(r_dir).exists():
        try:
            os.startfile(r_dir)
        except Exception as e:
            log_debug(f"Error abriendo carpeta desde tray: {e}")

def open_library_index():
    """Abre el catálogo index.html de la biblioteca en el navegador."""
    cfg = get_or_create_config()
    idx_file = Path(cfg.get("root_dir", "")) / "index.html"
    if idx_file.exists():
        webbrowser.open(f"file:///{idx_file.resolve().as_posix()}")
    else:
        open_documents_folder()

def quit_app_fully():
    """Cierra la aplicación por completo, deteniendo el tray y el servidor HTTP."""
    global tray_instance
    log_debug("quit_app_fully() invocado: cerrando tray y finalizando servidor...")
    if tray_instance:
        try:
            tray_instance.stop()
        except Exception as e:
            log_debug(f"Aviso deteniendo tray en quit_app_fully: {e}")
    schedule_shutdown(0.1)

def schedule_shutdown(delay: float = 4.0):
    """Programa un apagado diferido para permitir que reinicios de página o eventos cancelen el cierre."""
    global shutdown_scheduled_time
    shutdown_scheduled_time = time.time() + delay
    log_debug(f"Apagado programado en {delay}s (timestamp objetivo: {shutdown_scheduled_time})")

def cancel_scheduled_shutdown():
    """Cancela cualquier apagado programado cuando se detecta actividad legítima o ventana viva."""
    global shutdown_scheduled_time
    if shutdown_scheduled_time is not None:
        log_debug("Apagado programado CANCELADO por actividad de cliente o presencia de ventana.")
        shutdown_scheduled_time = None

def find_app_hwnds() -> list:
    """Busca en el sistema operativo Windows las ventanas nativas que pertenecen a Markdown to HTML."""
    results = []
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def enum_cb(hwnd, lparam):
            if user32.IsWindow(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    val = buff.value.strip()
                    if "Markdown to HTML" in val:
                        # Excluir editores o navegadores genéricos con el nombre en ruta/pestaña
                        if "Visual Studio Code" not in val and "Sublime" not in val:
                            results.append(hwnd)
            return True

        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception as e:
        log_debug(f"Aviso en find_app_hwnds: {e}")
    return results

def is_app_window_alive() -> bool:
    """
    Verifica si la ventana nativa de la aplicación sigue existiendo en el sistema operativo.
    Retorna:
      True  -> La ventana está confirmada como viva y abierta (activa, minimizada o en segundo plano).
      False -> La ventana existía previamente y el usuario la ha cerrado (HWND destruido).
      None  -> No se ha podido vincular a una ventana nativa de Windows (modo navegador externo o sin Win32).
    """
    global tracked_app_hwnds, initial_window_detected
    try:
        import ctypes
        user32 = ctypes.windll.user32

        # 1. Si ya teníamos HWNDs rastreados, verificar si al menos uno sigue siendo una ventana válida
        if tracked_app_hwnds:
            alive = {h for h in tracked_app_hwnds if user32.IsWindow(h)}
            tracked_app_hwnds = alive
            if tracked_app_hwnds:
                initial_window_detected = True
                return True

        # 2. Si no hay ventanas rastreadas o se perdieron, intentar descubrirlas activamente
        found = find_app_hwnds()
        if found:
            tracked_app_hwnds.update(found)
            initial_window_detected = True
            return True

        # 3. Si se había detectado una ventana previamente y ahora no existe ninguna
        if initial_window_detected:
            return False
        return None
    except Exception:
        return None

def extract_title_from_html(file_path: Path) -> str:
    """Extrae el título de un documento HTML buscando en caché o en la etiqueta <title>."""
    try:
        return md_engine.get_cached_title_or_read(file_path)
    except Exception:
        fallback = file_path.stem.replace("-", " ").replace("_", " ").capitalize()
        return fallback

def get_or_create_config() -> dict:
    config = {
        "root_dir": str(DEFAULT_ROOT_DIR),
        "auto_open": True,
        "system_tray_enabled": True,
        "close_to_tray": True,
        "first_tray_notification_shown": False,
        "recent_conversions": []
    }
    if not CONFIG_FILE.exists() and CONFIG_TEMPLATE_FILE.exists():
        try:
            with open(CONFIG_TEMPLATE_FILE, "r", encoding="utf-8") as f:
                template_data = json.load(f)
                config.update(template_data)
        except Exception:
            pass

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config.update(loaded)
        except Exception as e:
            print(f"Aviso: Error leyendo config.json, usando valores predeterminados: {e}")

    # Verificación defensiva y creación garantizada de la carpeta de destino
    root_path = Path(config.get("root_dir") or DEFAULT_ROOT_DIR)
    try:
        root_path.mkdir(parents=True, exist_ok=True)
        config["root_dir"] = str(root_path.resolve())
    except Exception as e:
        print(f"Error verificando ruta raíz '{root_path}', recurriendo a default: {e}")
        DEFAULT_ROOT_DIR.mkdir(parents=True, exist_ok=True)
        config["root_dir"] = str(DEFAULT_ROOT_DIR.resolve())
        root_path = DEFAULT_ROOT_DIR

    # Actualizar historial: filtrar archivos que sigan existiendo físicamente en disco
    raw_recents = config.get("recent_conversions", [])
    valid_recents = []
    known_paths = set()
    for item in raw_recents:
        fp_str = item.get("file_path")
        if fp_str:
            fp = Path(fp_str)
            if fp.is_file():
                valid_recents.append(item)
                try:
                    known_paths.add(str(fp.resolve()).lower())
                except Exception:
                    pass

    # Descubrir y recargar archivos HTML preexistentes en la carpeta raíz
    # Optimización: Solo evaluar candidatos ordenados por mtime para evitar re-lecturas masivas
    untracked_items = []
    if root_path.exists() and root_path.is_dir():
        candidates = []
        for f in root_path.glob("*.html"):
            if f.name.lower() in ("index.html", "latest.html"):
                continue
            try:
                resolved_f = str(f.resolve()).lower()
                if resolved_f not in known_paths:
                    candidates.append((f, f.stat().st_mtime))
            except Exception:
                continue

        if candidates:
            # Ordenar candidatos de más nuevo a más viejo por mtime
            candidates.sort(key=lambda x: x[1], reverse=True)
            # Solo procesar como máximo los 10 más recientes
            for f, mtime in candidates[:10]:
                try:
                    dt = datetime.fromtimestamp(mtime)
                    doc_title = extract_title_from_html(f)
                    untracked_items.append({
                        "item": {
                            "title": doc_title,
                            "filename": f.name,
                            "file_url": f"file:///{f.resolve().as_posix()}",
                            "file_path": str(f.resolve()),
                            "timestamp": dt.strftime("%d/%m/%Y %I:%M %p")
                        },
                        "mtime": mtime
                    })
                except Exception:
                    continue

    # Si hay archivos preexistentes no registrados, ordenarlos por fecha y anexarlos
    if untracked_items:
        untracked_items.sort(key=lambda x: x["mtime"], reverse=True)
        untracked_list = [entry["item"] for entry in untracked_items]
        if not valid_recents:
            valid_recents = untracked_list
        else:
            valid_recents.extend(untracked_list)

    config["recent_conversions"] = valid_recents[:10]

    save_config(config)

    # Mantener index.html en sincronía con los archivos reales existentes en disco (usando caché de metadatos)
    try:
        md_engine.generate_index_html(root_path)
    except Exception as ie:
        pass

    return config

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando config.json: {e}")

def add_recent_conversion(doc_info: dict):
    config = get_or_create_config()
    recents = config.get("recent_conversions", [])
    # Evitar duplicados por filename
    recents = [r for r in recents if r.get("filename") != doc_info.get("filename")]
    recents.insert(0, {
        "title": doc_info.get("title"),
        "filename": doc_info.get("filename"),
        "file_url": doc_info.get("file_url"),
        "file_path": doc_info.get("file_path"),
        "timestamp": doc_info.get("timestamp")
    })
    config["recent_conversions"] = recents[:10]
    save_config(config)

def choose_folder_native(initial_dir: str = "") -> str:
    """Abre el selector de carpetas nativo de Windows usando tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(
            title="Selecciona la carpeta raíz para guardar los documentos HTML",
            initialdir=initial_dir or str(Path.home() / "Downloads")
        )
        root.destroy()
        return folder
    except Exception as e:
        print(f"Error abriendo diálogo de carpeta: {e}")
        return ""

def choose_file_native() -> str:
    """Abre el selector de archivos .md nativo de Windows usando tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title="Selecciona un archivo Markdown",
            filetypes=[
                ("Archivos Markdown", "*.md *.markdown *.txt"),
                ("Todos los archivos", "*.*")
            ],
            initialdir=str(Path.home() / "Downloads")
        )
        root.destroy()
        return file_path
    except Exception as e:
        print(f"Error abriendo diálogo de archivo: {e}")
        return ""

class AppRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciar logs para máximo rendimiento y discreción
        pass

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global last_heartbeat, client_connected
        client_connected = True
        last_heartbeat = time.time()
        cancel_scheduled_shutdown()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path in ("/", "/index.html"):
            ui_file = UI_DIR / "index.html"
            if ui_file.exists():
                with open(ui_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if path.startswith("/assets/"):
            rel_name = path[len("/assets/"):]
            asset_file = (ASSETS_DIR / rel_name).resolve()
            if asset_file.exists() and ASSETS_DIR in asset_file.parents:
                suffix = asset_file.suffix.lower()
                if suffix == ".png":
                    mime = "image/png"
                elif suffix == ".ico":
                    mime = "image/x-icon"
                elif suffix == ".js":
                    mime = "application/javascript; charset=utf-8"
                elif suffix == ".css":
                    mime = "text/css; charset=utf-8"
                elif suffix == ".svg":
                    mime = "image/svg+xml"
                else:
                    mime = "application/octet-stream"
                with open(asset_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if path == "/api/config":
            config = get_or_create_config()
            self.send_json(config)
            return

        if path == "/api/logs":
            log_file = APP_DIR / "debug_log.txt"
            lines = []
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [l.rstrip() for l in f.readlines()[-80:]]
                except Exception:
                    pass
            self.send_json({"logs": lines})
            return

        if path == "/api/clipboard":
            text = get_clipboard_text()
            self.send_json({"text": text, "length": len(text)})
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        global last_heartbeat, client_connected
        client_connected = True
        last_heartbeat = time.time()
        cancel_scheduled_shutdown()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b""
        payload = {}
        if body_bytes:
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/heartbeat":
            self.send_json({"status": "alive"})
            return

        if path == "/api/clipboard":
            text = get_clipboard_text()
            self.send_json({"text": text, "length": len(text)})
            return

        if path == "/api/open-app":
            open_app_window()
            self.send_json({"status": "opened"})
            return

        if path == "/api/quit-app":
            quit_app_fully()
            self.send_json({"status": "quitting"})
            return

        if path == "/api/shutdown":
            reason = payload.get("reason", "")
            force = payload.get("force", False)
            cfg = get_or_create_config()
            if reason == "window_unload" and not force and cfg.get("system_tray_enabled", True) and cfg.get("close_to_tray", True):
                log_debug("Petición /api/shutdown con reason='window_unload'. Modo bandeja activo: preservando servidor.")
                if tray_instance and not cfg.get("first_tray_notification_shown", False):
                    try:
                        tray_instance.show_balloon(
                            title="Markdown to HTML",
                            message="La aplicación sigue activa en la bandeja del sistema. Haz clic en el icono para abrirla."
                        )
                    except Exception:
                        pass
                    cfg["first_tray_notification_shown"] = True
                    save_config(cfg)
                self.send_json({"status": "tray_preserved"})
                return

            delay = float(payload.get("delay", 4.0)) if isinstance(payload.get("delay"), (int, float)) else 4.0
            schedule_shutdown(delay=delay)
            self.send_json({"status": "scheduled", "delay": delay})
            return

        if path == "/api/open-logs":
            log_file = APP_DIR / "debug_log.txt"
            try:
                if not log_file.exists():
                    log_file.touch()
                os.startfile(str(log_file.resolve()))
                log_debug("POST /api/open-logs: archivo debug_log.txt abierto en el editor del sistema")
                self.send_json({"status": "opened"})
            except Exception as e:
                log_debug(f"Aviso abriendo logs: {e}")
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/adjust-window":
            sw = payload.get("screen_w")
            sh = payload.get("screen_h")
            tw, th, px, py = get_dynamic_window_geometry(sw, sh)
            threading.Thread(
                target=find_and_adjust_app_window,
                args=(tw, th, px, py),
                kwargs={"retries": 15},
                daemon=True
            ).start()
            self.send_json({
                "success": True,
                "target_w": tw,
                "target_h": th,
                "pos_x": px,
                "pos_y": py
            })
            return

        if path == "/api/config":
            config = get_or_create_config()
            if "root_dir" in payload and payload["root_dir"]:
                new_root = Path(payload["root_dir"]).resolve()
                try:
                    new_root.mkdir(parents=True, exist_ok=True)
                    config["root_dir"] = str(new_root)
                except Exception as e:
                    self.send_json({"error": f"No se pudo crear la carpeta: {e}"}, status=400)
                    return
            if "auto_open" in payload:
                config["auto_open"] = bool(payload["auto_open"])
            if "system_tray_enabled" in payload:
                config["system_tray_enabled"] = bool(payload["system_tray_enabled"])
            if "close_to_tray" in payload:
                config["close_to_tray"] = bool(payload["close_to_tray"])
            save_config(config)
            self.send_json(config)
            return

        if path == "/api/browse-folder":
            config = get_or_create_config()
            chosen = choose_folder_native(config.get("root_dir", ""))
            if chosen:
                chosen_p = Path(chosen).resolve()
                chosen_p.mkdir(parents=True, exist_ok=True)
                config["root_dir"] = str(chosen_p)
                save_config(config)
                log_debug(f"POST /api/browse-folder: nueva ruta raíz '{chosen_p}'")
                self.send_json({"chosen_path": str(chosen_p)})
            else:
                self.send_json({"chosen_path": None})
            return

        if path == "/api/browse-file":
            chosen = choose_file_native()
            if chosen:
                chosen_p = Path(chosen).resolve()
                log_debug(f"POST /api/browse-file: archivo seleccionado '{chosen_p.name}'")
                self.send_json({
                    "file_path": str(chosen_p),
                    "filename": chosen_p.name
                })
            else:
                self.send_json({"file_path": None})
            return

        if path == "/api/convert":
            t0 = time.time()
            config = get_or_create_config()
            root_dir = config.get("root_dir", str(DEFAULT_ROOT_DIR))
            custom_title = payload.get("custom_title", "").strip() or None
            auto_open = payload.get("auto_open", config.get("auto_open", True))

            md_content = ""
            input_file = payload.get("file_path")
            if input_file and Path(input_file).exists():
                try:
                    with open(input_file, "r", encoding="utf-8-sig", errors="replace") as f:
                        md_content = f.read()
                    log_debug(f"POST /api/convert: archivo '{Path(input_file).name}' ({len(md_content)} caracteres)")
                except Exception as e:
                    log_debug(f"ERROR leyendo archivo {input_file}: {e}")
                    self.send_json({"error": f"Error leyendo el archivo: {e}"}, status=400)
                    return
            else:
                md_content = payload.get("text", "")
                sample = md_content[:50].replace('\n', ' ') if md_content else ''
                log_debug(f"POST /api/convert: texto ({len(md_content)} caracteres) - '{sample}'")

            if not md_content.strip():
                log_debug("Aviso en /api/convert: texto vacío recibido")
                self.send_json({"error": "No se recibió texto Markdown para convertir."}, status=400)
                return

            try:
                res = md_engine.convert_and_update_library(
                    md_text=md_content,
                    root_dir_str=root_dir,
                    custom_title=custom_title,
                    input_file_path=input_file
                )
                add_recent_conversion(res)

                elapsed_ms = (time.time() - t0) * 1000
                log_debug(f"Conversión exitosa en {elapsed_ms:.1f}ms: '{res.get('title')}' -> {res.get('filename')}")

                if auto_open:
                    try:
                        webbrowser.open(res["file_url"])
                    except Exception as we:
                        log_debug(f"Aviso: Error abriendo navegador: {we}")

                self.send_json(res)
            except Exception as e:
                import traceback
                err_tb = traceback.format_exc()
                log_debug(f"ERROR CRÍTICO en conversión tras {(time.time() - t0)*1000:.1f}ms: {e}\n{err_tb}")
                self.send_json({"error": f"Error en la conversión: {e}"}, status=500)
            return

        if path == "/api/open-file":
            url = payload.get("url", "")
            if url:
                try:
                    webbrowser.open(url)
                    self.send_json({"status": "opened"})
                except Exception as e:
                    self.send_json({"error": str(e)}, status=500)
            else:
                self.send_json({"error": "No URL provided"}, status=400)
            return

        if path == "/api/open-folder":
            config = get_or_create_config()
            rdir = config.get("root_dir", str(DEFAULT_ROOT_DIR))
            try:
                os.startfile(rdir)
                self.send_json({"status": "opened"})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/open-index":
            config = get_or_create_config()
            rdir = Path(config.get("root_dir", str(DEFAULT_ROOT_DIR)))
            index_path = rdir / "index.html"
            if not index_path.exists():
                md_engine.generate_index_html(rdir)
            index_url = f"file:///{index_path.resolve().as_posix()}"
            try:
                webbrowser.open(index_url)
                self.send_json({"status": "opened", "url": index_url})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
            return

        if path == "/api/delete-document":
            config = get_or_create_config()
            root_dir = Path(config.get("root_dir", str(DEFAULT_ROOT_DIR)))
            filename = payload.get("filename", "").strip()
            file_path_str = payload.get("file_path", "").strip()

            # Seguridad defensiva previa: rechazar archivos protegidos o extensiones ajenas
            target_name = (file_path_str and Path(file_path_str).name) or filename
            if target_name.lower() in ("index.html", "latest.html") or (target_name and Path(target_name).suffix.lower() not in (".html", ".htm")):
                self.send_json({"error": "Archivo protegido o no permitido para eliminación."}, status=400)
                return

            target_file = None
            if file_path_str:
                p = Path(file_path_str).resolve()
                if p.exists() and p.is_file():
                    target_file = p
            elif filename:
                p = (root_dir / filename).resolve()
                if p.exists() and p.is_file():
                    target_file = p

            if target_file:
                try:
                    target_file.unlink()
                except Exception as e:
                    self.send_json({"error": f"Error eliminando archivo: {e}"}, status=500)
                    return

            # Remover de recent_conversions
            recents = config.get("recent_conversions", [])
            recents = [r for r in recents if r.get("filename") != filename and r.get("file_path") != file_path_str]
            config["recent_conversions"] = recents
            save_config(config)

            # Eliminar del caché de índice
            try:
                if filename:
                    md_engine.remove_from_index_cache(root_dir, filename)
                elif file_path_str:
                    md_engine.remove_from_index_cache(root_dir, Path(file_path_str).name)
            except Exception:
                pass

            # Regenerar catálogo index.html y latest.html en la biblioteca
            try:
                md_engine.generate_index_html(root_dir)
                rem = [f for f in root_dir.glob("*.html") if f.name.lower() not in ("index.html", "latest.html")]
                if rem:
                    rem.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    newest = rem[0]
                    newest_title = extract_title_from_html(newest)
                    md_engine.generate_latest_redirect(root_dir, newest, newest_title)
                else:
                    latest_p = root_dir / "latest.html"
                    if latest_p.exists():
                        latest_p.unlink()
            except Exception as e:
                print(f"Aviso actualizando biblioteca tras eliminación: {e}")

            self.send_json({
                "success": True,
                "filename": filename,
                "recent_conversions": config["recent_conversions"]
            })
            return

        self.send_response(404)
        self.end_headers()

def watchdog_thread(server: HTTPServer):
    """
    Guardián defensivo de ciclo de vida con detección nativa de ventanas de Windows.
    Garantiza que el servidor permanezca vivo mientras la ventana esté abierta (incluso si está
    en segundo plano o inactiva por horas), y apaga el proceso limpiamente cuando la ventana se cierra.
    """
    global last_heartbeat, client_connected, shutdown_scheduled_time
    start_time = time.time()

    # 1. Esperar hasta 120 segundos a que el navegador cargue la página por primera vez
    while not client_connected:
        time.sleep(1)
        if time.time() - start_time > 120:
            log_debug("No se detectó conexión inicial en 120s. Apagando servidor.")
            server.shutdown()
            return

    log_debug("Watchdog: Frontend conectado con éxito. Iniciando supervisión activa.")

    # 2. Bucle de supervisión continua
    while True:
        time.sleep(2)
        now = time.time()

        # Regla de oro: Si el cliente está enviando peticiones/latidos activamente (hace menos de 10s),
        # la aplicación está 100% activa. Cancelar cualquier apagado programado y continuar.
        if now - last_heartbeat < 10:
            cancel_scheduled_shutdown()
            continue

        # Caso 1: Señal explícita de apagado recibida (/api/shutdown via beacon o /api/quit-app)
        if shutdown_scheduled_time is not None:
            if now >= shutdown_scheduled_time:
                log_debug("Apagado ordenado ejecutado tras recibir señal de cierre.")
                server.shutdown()
                break
            continue

        # Caso 2: Inactividad prolongada sin latidos por más de 180s (3 minutos)
        if now - last_heartbeat > 180:
            window_status = is_app_window_alive()
            if window_status is True:
                # La ventana sigue viva en el SO (ej. en segundo plano o minimizada)
                # No apagar, mantener vivo y renovar heartbeat
                last_heartbeat = now
                continue
            else:
                cfg = get_or_create_config()
                if cfg.get("system_tray_enabled", True) and cfg.get("close_to_tray", True):
                    # En modo bandeja, permanecer en reposo sin apagar el servidor
                    time.sleep(2)
                    continue
                log_debug("Inactividad prolongada sin latidos ni ventana abierta (180s). Apagando servidor...")
                server.shutdown()
                break

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def get_server_port(preferred_port: int = DEFAULT_PORT) -> int:
    """
    Intenta utilizar un puerto fijo preferido (51870) para mantener constante el origen
    (http://127.0.0.1:51870) en Microsoft Edge / Chromium. Si dicho puerto ya está ocupado
    por otra instancia o servicio, encuentra un puerto libre efímero dinámicamente.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', preferred_port))
            return preferred_port
    except OSError:
        pass

    return find_free_port()

def get_clipboard_text() -> str:
    """
    Obtiene el texto del portapapeles nativo de Windows vía Win32 API.
    Zero-bloatware, sin dependencias externas y sin disparar alertas de permisos del navegador.
    """
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

def get_dynamic_window_geometry(screen_w: int = None, screen_h: int = None):
    """Calcula las dimensiones ideales de la ventana según la resolución de la pantalla."""
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
        # Monitor grande (Escritorio / 1080p+, 2K, 4K):
        # Iniciar más pequeño y compacto, ideal para multitarea
        target_w = 750
        target_h = min(680, max(560, int(screen_h * 0.68)))
    else:
        # Laptop o pantalla mediana/pequeña (< 1600px de ancho, ej. 1366x768, 1280x720, 1440x900):
        # Iniciar más o menos grande (85% ancho y 86% alto disponible)
        target_w = max(680, min(1280, int(screen_w * 0.85)))
        target_h = max(560, min(760, int(screen_h * 0.86)))

    pos_x = max(0, (screen_w - target_w) // 2)
    pos_y = max(0, (screen_h - target_h) // 2)
    return target_w, target_h, pos_x, pos_y

def find_and_adjust_app_window(target_w: int, target_h: int, pos_x: int = None, pos_y: int = None, retries: int = 25):
    """Localiza la ventana de Edge/Chrome de la app y ajusta su tamaño y posición nativa."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        SW_RESTORE = 9
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        for _ in range(retries):
            found_hwnds = []

            def enum_cb(hwnd, lparam):
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
                global tracked_app_hwnds, initial_window_detected
                tracked_app_hwnds.update(found_hwnds)
                initial_window_detected = True
                for hwnd in found_hwnds:
                    # Desmaximizar si el navegador recordó estado maximizado
                    user32.ShowWindow(hwnd, SW_RESTORE)

                    # Centrar respetando el monitor donde está la ventana
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
                        hwnd, 0,
                        final_x, final_y,
                        target_w, target_h,
                        SWP_NOZORDER | SWP_SHOWWINDOW
                    )
                log_debug(f"Ventana ajustada nativamente a {target_w}x{target_h}")
                return True

            time.sleep(0.2)
    except Exception as e:
        log_debug(f"Aviso ajustando geometría de ventana: {e}")
    return False

def launch_desktop_window(port: int):
    """Lanza la ventana de la app usando Microsoft Edge en modo aplicación o navegador."""
    url = f"http://127.0.0.1:{port}"
    target_w, target_h, pos_x, pos_y = get_dynamic_window_geometry()

    edge_candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    target_exe = None
    for cand in edge_candidates + chrome_candidates:
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
            log_debug(f"Iniciando ventana de app ({target_w}x{target_h} @ {pos_x},{pos_y}): {' '.join(cmd)}")
            subprocess.Popen(cmd)

            # Hilo defensivo para garantizar el tamaño en caso de restaurar estado previo
            threading.Thread(
                target=find_and_adjust_app_window,
                args=(target_w, target_h, pos_x, pos_y),
                daemon=True
            ).start()
            return
        except Exception as e:
            log_debug(f"Aviso al lanzar modo app: {e}")

    # Fallback al navegador predeterminado
    log_debug(f"Abriendo navegador predeterminado: {url}")
    webbrowser.open(url)

_log_lock = threading.Lock()

def log_debug(msg: str):
    """Escribe registros defensivos en debug_log.txt de forma segura entre hilos con rotación."""
    log_file = APP_DIR / "debug_log.txt"
    try:
        with _log_lock:
            if log_file.exists() and log_file.stat().st_size > 1_000_000:
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as rf:
                        rf.seek(max(0, log_file.stat().st_size - 250_000))
                        tail = rf.read()
                    with open(log_file, "w", encoding="utf-8") as wf:
                        wf.write(f"--- [REGISTRO ROTADO] ---\n{tail}")
                except Exception:
                    pass
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}\n")
    except Exception:
        pass

def main():
    global client_connected, last_heartbeat, current_server_port, tray_instance, app_single_instance_mutex
    log_debug("--- Inicio de main() ---")

    # 1. Candado de instancia única
    app_single_instance_mutex = acquire_single_instance_lock()
    if app_single_instance_mutex is None:
        log_debug("Proceso secundario finalizado: instancia primaria ya activa.")
        sys.exit(0)

    cfg = get_or_create_config()
    log_debug("Configuración obtenida/creada")
    port = get_server_port()
    current_server_port = port
    log_debug(f"Puerto asignado: {port}")
    last_heartbeat = time.time()
    
    server = ThreadingHTTPServer(('127.0.0.1', port), AppRequestHandler)
    log_debug("ThreadingHTTPServer instanciado")
    
    t_watchdog = threading.Thread(target=watchdog_thread, args=(server,), daemon=True)
    t_watchdog.start()
    log_debug("Watchdog iniciado en hilo daemon")

    # 2. Inicializar System Tray si está habilitado
    if cfg.get("system_tray_enabled", True):
        try:
            icon_path = ASSETS_DIR / "app_icon.ico"
            tray_instance = tray_manager.TrayManager(
                icon_path=icon_path,
                tooltip="Markdown to HTML — Desktop App",
                on_open_app=open_app_window,
                on_open_folder=open_documents_folder,
                on_open_index=open_library_index,
                on_quit=quit_app_fully,
                log_callback=log_debug
            )
            tray_instance.start()
            log_debug("TrayManager iniciado en hilo daemon")
        except Exception as e:
            log_debug(f"Aviso al iniciar TrayManager: {e}")

    log_debug(f"Llamando a launch_desktop_window({port})...")
    launch_desktop_window(port)
    log_debug("launch_desktop_window completado")

    log_debug("Entrando a server.serve_forever()...")
    try:
        server.serve_forever()
        log_debug("server.serve_forever() terminó de forma natural")
    except Exception as e:
        log_debug(f"Excepción en serve_forever: {e}")
    finally:
        log_debug("Bloque finally de main(): cerrando servidor y tray")
        if tray_instance:
            try:
                tray_instance.stop()
            except Exception:
                pass
        if app_single_instance_mutex:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(app_single_instance_mutex)
            except Exception:
                pass
        server.server_close()

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        crash_file = APP_DIR / "crash_log.txt"
        with open(crash_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- CRASH {datetime.now()} ---\n")
            f.write(traceback.format_exc())


