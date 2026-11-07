#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP REST API and static SPA asset request handlers.
Uses HttpRouter to dispatch incoming requests to focused, single-purpose methods.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
from typing import Any, Dict
from urllib.parse import urlparse
import webbrowser

from md2html.adapters.http.router import HttpRouter
from md2html.adapters.storage.logger import log_debug, read_recent_logs
from md2html.core.services.catalog_service import (
    delete_document_from_library,
    generate_index_html,
)
from md2html.core.services.conversion_service import convert_and_update_library

router = HttpRouter()

_MIME_TYPES: Dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
}


class AppRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the desktop SPA and REST API.
    Delegates OS/config state interactions through `runtime_facade` (bound to `app`).
    """

    runtime_facade: Any = None

    @property
    def _rt(self) -> Any:
        if self.runtime_facade is not None:
            return self.runtime_facade
        if "app" in sys.modules:
            return sys.modules["app"]
        if "__main__" in sys.modules and hasattr(sys.modules["__main__"], "_lifecycle"):
            return sys.modules["__main__"]
        import app

        return app

    def log_message(self, format: str, *args: Any) -> None:
        """Suppresses standard stderr HTTP logging for silent background operation."""
        pass

    def send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        """Serializes a dictionary as UTF-8 JSON and writes the HTTP response."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static_file(self, file_path: Path) -> bool:
        """Serves a static file with appropriate MIME headers if it exists."""
        if not file_path.exists() or not file_path.is_file():
            return False
        mime = _MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
        return True

    def _record_request_activity(self) -> str:
        rt = self._rt
        rt.client_connected = True
        rt.last_heartbeat = time.time()
        rt.cancel_scheduled_shutdown(force=False)
        return urlparse(self.path).path

    def do_GET(self) -> None:
        path = self._record_request_activity()
        handler = router.resolve("GET", path)
        if handler is not None:
            handler(self, {})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        path = self._record_request_activity()
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b""
        payload: Dict[str, Any] = {}
        if body_bytes:
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        handler = router.resolve("POST", path)
        if handler is not None:
            handler(self, payload)
            return
        self.send_response(404)
        self.end_headers()


# ---------------------------------------------------------------------------
# GET Route Handlers
# ---------------------------------------------------------------------------


@router.get("/", "/index.html")
def _handle_get_spa(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    ui_file = req._rt.UI_DIR / "index.html"
    if not req._serve_static_file(ui_file):
        req.send_response(404)
        req.end_headers()


@router.get("/styles.css", "/ui/styles.css")
def _handle_get_ui_styles(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    css_file = req._rt.UI_DIR / "styles.css"
    if not req._serve_static_file(css_file):
        req.send_response(404)
        req.end_headers()


@router.get("/app.js", "/ui/app.js")
def _handle_get_ui_js(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    js_file = req._rt.UI_DIR / "app.js"
    if not req._serve_static_file(js_file):
        req.send_response(404)
        req.end_headers()


def _handle_get_asset(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    path = urlparse(req.path).path
    rel_name = path[len("/assets/") :]
    assets_dir = req._rt.ASSETS_DIR
    asset_file = (assets_dir / rel_name).resolve()
    if asset_file.exists() and assets_dir in asset_file.parents:
        if req._serve_static_file(asset_file):
            return
    req.send_response(404)
    req.end_headers()


router.add_prefix_route("GET", "/assets/", _handle_get_asset)


@router.get("/api/config")
def _handle_get_config(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    config = req._rt.get_or_create_config()
    req.send_json(config)


@router.get("/api/logs")
def _handle_get_logs(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    log_file = req._rt.APP_DIR / "debug_log.txt"
    req.send_json({"logs": read_recent_logs(log_file)})


@router.get("/api/clipboard")
def _handle_get_clipboard(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    text = req._rt.get_clipboard_text()
    req.send_json({"text": text, "length": len(text)})


# ---------------------------------------------------------------------------
# POST Route Handlers
# ---------------------------------------------------------------------------


@router.post("/api/heartbeat")
def _handle_post_heartbeat(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    req.send_json({"status": "alive"})


@router.post("/api/clipboard")
def _handle_post_clipboard(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    text = req._rt.get_clipboard_text()
    req.send_json({"text": text, "length": len(text)})


@router.post("/api/open-app")
def _handle_post_open_app(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    req._rt.open_app_window()
    req.send_json({"status": "opened"})


@router.post("/api/quit-app")
def _handle_post_quit_app(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    req._rt.quit_app_fully()
    req.send_json({"status": "quitting"})


@router.post("/api/close-window")
def _handle_post_close_window(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    closed = req._rt.close_app_window()
    req.send_json({"success": True, "closed": closed})


@router.post("/api/shutdown")
def _handle_post_shutdown(req: AppRequestHandler, payload: Dict[str, Any]) -> None:
    rt = req._rt
    reason = payload.get("reason", "")
    force = payload.get("force", False)
    cfg = rt.get_or_create_config()

    if (
        reason == "window_unload"
        and not force
        and cfg.get("system_tray_enabled", True)
        and cfg.get("close_to_tray", True)
    ):
        log_debug(
            "Petición /api/shutdown con reason='window_unload'. Modo bandeja activo: preservando servidor."
        )
        if rt.tray_instance and not cfg.get("first_tray_notification_shown", False):
            try:
                rt.tray_instance.show_balloon(
                    title="Markdown to HTML",
                    message="La aplicación sigue activa en la bandeja del sistema. Haz clic en el icono para abrirla.",
                )
            except Exception:
                pass
            cfg["first_tray_notification_shown"] = True
            rt.save_config(cfg)
        req.send_json({"status": "tray_preserved"})
        return

    delay = (
        float(payload.get("delay", 4.0))
        if isinstance(payload.get("delay"), (int, float))
        else 4.0
    )
    rt.schedule_shutdown(delay=delay)
    req.send_json({"status": "scheduled", "delay": delay})


@router.post("/api/open-logs")
def _handle_post_open_logs(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    log_file = req._rt.APP_DIR / "debug_log.txt"
    try:
        if not log_file.exists():
            log_file.touch()
        os.startfile(str(log_file.resolve()))
        log_debug("POST /api/open-logs: archivo debug_log.txt abierto en el editor del sistema")
        req.send_json({"status": "opened"})
    except Exception as e:
        log_debug(f"Aviso abriendo logs: {e}")
        req.send_json({"error": str(e)}, status=500)


@router.post("/api/adjust-window")
def _handle_post_adjust_window(req: AppRequestHandler, payload: Dict[str, Any]) -> None:
    rt = req._rt
    sw = payload.get("screen_w")
    sh = payload.get("screen_h")
    tw, th, px, py = rt.get_dynamic_window_geometry(sw, sh)
    threading.Thread(
        target=rt.find_and_adjust_app_window,
        args=(tw, th, px, py),
        kwargs={"retries": 15},
        daemon=True,
    ).start()
    req.send_json(
        {
            "success": True,
            "target_w": tw,
            "target_h": th,
            "pos_x": px,
            "pos_y": py,
        }
    )


@router.post("/api/config")
def _handle_post_config(req: AppRequestHandler, payload: Dict[str, Any]) -> None:
    rt = req._rt
    config = rt.get_or_create_config()
    if "root_dir" in payload and payload["root_dir"]:
        new_root = Path(payload["root_dir"]).resolve()
        try:
            new_root.mkdir(parents=True, exist_ok=True)
            config["root_dir"] = str(new_root)
        except Exception as e:
            req.send_json({"error": f"No se pudo crear la carpeta: {e}"}, status=400)
            return
    if "auto_open" in payload:
        config["auto_open"] = bool(payload["auto_open"])
    if "close_on_convert" in payload:
        config["close_on_convert"] = bool(payload["close_on_convert"])
    if "system_tray_enabled" in payload:
        config["system_tray_enabled"] = bool(payload["system_tray_enabled"])
    if "close_to_tray" in payload:
        config["close_to_tray"] = bool(payload["close_to_tray"])
    rt.save_config(config)
    req.send_json(config)


@router.post("/api/browse-folder")
def _handle_post_browse_folder(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    rt = req._rt
    config = rt.get_or_create_config()
    chosen = rt.choose_folder_native(config.get("root_dir", ""))
    if chosen:
        chosen_p = Path(chosen).resolve()
        chosen_p.mkdir(parents=True, exist_ok=True)
        config["root_dir"] = str(chosen_p)
        rt.save_config(config)
        log_debug(f"POST /api/browse-folder: nueva ruta raíz '{chosen_p}'")
        req.send_json({"chosen_path": str(chosen_p)})
    else:
        req.send_json({"chosen_path": None})


@router.post("/api/browse-file")
def _handle_post_browse_file(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    chosen = req._rt.choose_file_native()
    if chosen:
        chosen_p = Path(chosen).resolve()
        log_debug(f"POST /api/browse-file: archivo seleccionado '{chosen_p.name}'")
        req.send_json({"file_path": str(chosen_p), "filename": chosen_p.name})
    else:
        req.send_json({"file_path": None})


@router.post("/api/convert")
def _handle_post_convert(req: AppRequestHandler, payload: Dict[str, Any]) -> None:
    rt = req._rt
    t0 = time.time()
    config = rt.get_or_create_config()
    root_dir = config.get("root_dir", str(rt.DEFAULT_ROOT_DIR))
    custom_title = payload.get("custom_title", "").strip() or None
    auto_open = payload.get("auto_open", config.get("auto_open", True))

    md_content = ""
    input_file = payload.get("file_path")
    if input_file and Path(input_file).exists():
        try:
            with open(input_file, "r", encoding="utf-8-sig", errors="replace") as f:
                md_content = f.read()
            log_debug(
                f"POST /api/convert: archivo '{Path(input_file).name}' ({len(md_content)} caracteres)"
            )
        except Exception as e:
            log_debug(f"ERROR leyendo archivo {input_file}: {e}")
            req.send_json({"error": f"Error leyendo el archivo: {e}"}, status=400)
            return
    else:
        md_content = payload.get("text", "")
        sample = md_content[:50].replace("\n", " ") if md_content else ""
        log_debug(f"POST /api/convert: texto ({len(md_content)} caracteres) - '{sample}'")

    if not md_content.strip():
        log_debug("Aviso en /api/convert: texto vacío recibido")
        req.send_json({"error": "No se recibió texto Markdown para convertir."}, status=400)
        return

    try:
        res = convert_and_update_library(
            md_text=md_content,
            root_dir_str=root_dir,
            custom_title=custom_title,
            input_file_path=input_file,
        )
        rt.add_recent_conversion(res)

        elapsed_ms = (time.time() - t0) * 1000
        log_debug(
            f"Conversión exitosa en {elapsed_ms:.1f}ms: '{res.get('title')}' -> {res.get('filename')}"
        )

        if auto_open:
            try:
                webbrowser.open(res["file_url"])
            except Exception as we:
                log_debug(f"Aviso: Error abriendo navegador: {we}")

        req.send_json(res)
    except Exception as e:
        err_tb = traceback.format_exc()
        log_debug(
            f"ERROR CRÍTICO en conversión tras {(time.time() - t0) * 1000:.1f}ms: {e}\n{err_tb}"
        )
        req.send_json({"error": f"Error en la conversión: {e}"}, status=500)


@router.post("/api/open-file")
def _handle_post_open_file(req: AppRequestHandler, payload: Dict[str, Any]) -> None:
    url = payload.get("url", "")
    if url:
        try:
            webbrowser.open(url)
            req.send_json({"status": "opened"})
        except Exception as e:
            req.send_json({"error": str(e)}, status=500)
    else:
        req.send_json({"error": "No URL provided"}, status=400)


@router.post("/api/open-folder")
def _handle_post_open_folder(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    rt = req._rt
    config = rt.get_or_create_config()
    rdir = config.get("root_dir", str(rt.DEFAULT_ROOT_DIR))
    try:
        os.startfile(rdir)
        req.send_json({"status": "opened"})
    except Exception as e:
        req.send_json({"error": str(e)}, status=500)


@router.post("/api/open-index")
def _handle_post_open_index(req: AppRequestHandler, _payload: Dict[str, Any]) -> None:
    rt = req._rt
    config = rt.get_or_create_config()
    rdir = Path(config.get("root_dir", str(rt.DEFAULT_ROOT_DIR)))
    index_path = rdir / "index.html"
    if not index_path.exists():
        generate_index_html(rdir)
    index_url = f"file:///{index_path.resolve().as_posix()}"
    try:
        webbrowser.open(index_url)
        req.send_json({"status": "opened", "url": index_url})
    except Exception as e:
        req.send_json({"error": str(e)}, status=500)


@router.post("/api/delete-document")
def _handle_post_delete_document(req: AppRequestHandler, payload: Dict[str, Any]) -> None:
    rt = req._rt
    config = rt.get_or_create_config()
    root_dir = Path(config.get("root_dir", str(rt.DEFAULT_ROOT_DIR)))
    filename = payload.get("filename", "").strip()
    file_path_str = payload.get("file_path", "").strip()

    status_code, response_body = delete_document_from_library(
        root_dir=root_dir,
        filename=filename,
        file_path_str=file_path_str,
        config=config,
        save_config_fn=rt.save_config,
    )
    req.send_json(response_body, status=status_code)
