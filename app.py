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
from http.server import HTTPServer, BaseHTTPRequestHandler
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

APP_DIR = Path(__file__).resolve().parent
UI_DIR = APP_DIR / "ui"
ASSETS_DIR = APP_DIR / "assets"
CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_ROOT_DIR = Path.home() / "Downloads" / "Markdown_HTML_Library"

# Estado global
last_heartbeat = time.time()
server_instance = None

def get_or_create_config() -> dict:
    config = {
        "root_dir": str(DEFAULT_ROOT_DIR),
        "auto_open": True,
        "recent_conversions": []
    }
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

    # Actualizar historial: filtrar únicamente archivos que sigan existiendo físicamente en disco
    raw_recents = config.get("recent_conversions", [])
    valid_recents = []
    for item in raw_recents:
        fp = item.get("file_path")
        if fp and Path(fp).is_file():
            valid_recents.append(item)
    config["recent_conversions"] = valid_recents

    save_config(config)

    # Mantener index.html en sincronía con los archivos reales existentes en disco
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
                mime = "image/png" if asset_file.suffix.lower() == ".png" else "application/octet-stream"
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

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        global last_heartbeat, client_connected
        client_connected = True
        last_heartbeat = time.time()
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
                self.send_json({"chosen_path": str(chosen_p)})
            else:
                self.send_json({"chosen_path": None})
            return

        if path == "/api/browse-file":
            chosen = choose_file_native()
            if chosen:
                chosen_p = Path(chosen).resolve()
                self.send_json({
                    "file_path": str(chosen_p),
                    "filename": chosen_p.name
                })
            else:
                self.send_json({"file_path": None})
            return

        if path == "/api/convert":
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
                except Exception as e:
                    self.send_json({"error": f"Error leyendo el archivo: {e}"}, status=400)
                    return
            else:
                md_content = payload.get("text", "")

            if not md_content.strip():
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

                if auto_open:
                    try:
                        webbrowser.open(res["file_url"])
                    except Exception as we:
                        print(f"Aviso: Error abriendo navegador: {we}")

                self.send_json(res)
            except Exception as e:
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

            target_file = None
            if file_path_str:
                p = Path(file_path_str).resolve()
                if p.exists() and p.is_file():
                    target_file = p
            elif filename:
                p = (root_dir / filename).resolve()
                if p.exists() and p.is_file():
                    target_file = p

            # Seguridad defensiva: solo borrar archivos .html de la biblioteca, nunca index/latest ni archivos ajenos
            if target_file:
                if target_file.name.lower() in ("index.html", "latest.html") or target_file.suffix.lower() not in (".html", ".htm"):
                    self.send_json({"error": "Archivo protegido o no permitido para eliminación."}, status=400)
                    return
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

            # Regenerar catálogo index.html y latest.html en la biblioteca
            try:
                md_engine.generate_index_html(root_dir)
                rem = [f for f in root_dir.glob("*.html") if f.name.lower() not in ("index.html", "latest.html")]
                if rem:
                    rem.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    newest = rem[0]
                    newest_title = newest.stem.replace("-", " ").capitalize()
                    try:
                        with open(newest, "r", encoding="utf-8", errors="ignore") as fh:
                            m = re.search(r'<title>(.*?)</title>', fh.read(4000), re.IGNORECASE)
                            if m and m.group(1).strip():
                                newest_title = m.group(1).strip()
                    except Exception:
                        pass
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

client_connected = False

def watchdog_thread(server: HTTPServer):
    """Monitorea el latido del frontend. Espera la conexión inicial antes de contar inactividad."""
    global last_heartbeat, client_connected
    start_time = time.time()
    # Esperar hasta 120 segundos a que el navegador cargue la página por primera vez
    while not client_connected:
        time.sleep(1)
        if time.time() - start_time > 120:
            print("No se detectó conexión inicial en 120s. Apagando servidor.")
            server.shutdown()
            return

    # Una vez conectado, si pasan más de 30 segundos sin ningún latido o petición, apagar
    while True:
        time.sleep(3)
        if time.time() - last_heartbeat > 30:
            print("Cierre de ventana detectado (30s sin latidos). Apagando servidor...")
            server.shutdown()
            break

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

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

def log_debug(msg: str):
    log_file = APP_DIR / "debug_log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {msg}\n")

def main():
    global client_connected, last_heartbeat
    log_debug("--- Inicio de main() ---")
    get_or_create_config()
    log_debug("Configuración obtenida/creada")
    port = find_free_port()
    log_debug(f"Puerto asignado: {port}")
    last_heartbeat = time.time()
    
    server = HTTPServer(('127.0.0.1', port), AppRequestHandler)
    log_debug("HTTPServer instanciado")
    
    t_watchdog = threading.Thread(target=watchdog_thread, args=(server,), daemon=True)
    t_watchdog.start()
    log_debug("Watchdog iniciado en hilo daemon")

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
        log_debug("Bloque finally de main(): cerrando servidor")
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


