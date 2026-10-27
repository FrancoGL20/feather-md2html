#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for HTTP Server API Endpoints (app.py).
Tests REST endpoints, status codes, JSON request/response bodies,
headers, file conversions, deletions, and error cases over live loopback HTTP.
"""

import os
import sys
import json
import time
import socket
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

# Add app directory to sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app
import md_engine
from tests.test_helpers import IsolatedEnvironmentTestCase


class TestAppAPI(IsolatedEnvironmentTestCase):
    """Live HTTP Server integration test suite."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        # Bind server to port 0 (OS allocates free ephemeral port)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), app.AppRequestHandler)
        self.port = self.server.server_port
        self.base_url = f"http://127.0.0.1:{self.port}"
        
        # Start server in background thread
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)
        super().tearDown()

    def _http_get(self, path: str):
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                headers = dict(response.headers)
                body = response.read()
                return status, headers, body
        except urllib.error.HTTPError as e:
            try:
                body = e.read()
                return e.code, dict(e.headers), body
            finally:
                e.close()

    def _http_post_json(self, path: str, payload: dict = None):
        url = f"{self.base_url}{path}"
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
                headers = dict(response.headers)
                body = response.read()
                try:
                    data = json.loads(body.decode("utf-8"))
                except Exception:
                    data = body
                return status, headers, data
        except urllib.error.HTTPError as e:
            try:
                body = e.read()
                try:
                    data = json.loads(body.decode("utf-8"))
                except Exception:
                    data = body
                return e.code, dict(e.headers), data
            finally:
                e.close()

    def test_get_root_serves_spa_html(self):
        status, headers, body = self._http_get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        body_text = body.decode("utf-8")
        self.assertIn("<title>", body_text)
        self.assertIn("Markdown", body_text)
        self.assertIn("pasteAndConvertBtn", body_text)
        self.assertIn("dual-action-grid", body_text)

    def test_get_assets_serves_existing_icon(self):
        status, headers, body = self._http_get("/assets/app_icon.png")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Content-Type"), "image/png")
        self.assertGreater(len(body), 0)

    def test_get_assets_not_found(self):
        status, headers, body = self._http_get("/assets/non_existent_image.png")
        self.assertEqual(status, 404)

    def test_get_assets_serves_mermaid_js(self):
        status, headers, body = self._http_get("/assets/mermaid.min.js")
        self.assertEqual(status, 200)
        self.assertIn("application/javascript", headers.get("Content-Type", ""))
        self.assertGreater(len(body), 1000000)

    def test_get_config_returns_json(self):
        status, headers, data = self._http_get("/api/config")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        self.assertIn("root_dir", json.loads(data.decode("utf-8")))

    def test_post_heartbeat(self):
        status, headers, data = self._http_post_json("/api/heartbeat")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "alive")

    def test_post_config_updates_settings(self):
        # Update auto_open and root_dir
        new_dir = self.temp_dir / "custom_lib"
        new_dir.mkdir(parents=True, exist_ok=True)
        
        status, _, data = self._http_post_json("/api/config", {
            "root_dir": str(new_dir),
            "auto_open": False
        })
        self.assertEqual(status, 200)
        self.assertFalse(data.get("auto_open"))
        self.assertEqual(str(Path(data.get("root_dir")).resolve()), str(new_dir.resolve()))

        # Verify persistence in config file
        saved_cfg = json.loads(self.test_config.read_text(encoding="utf-8"))
        self.assertFalse(saved_cfg.get("auto_open"))

    def test_post_convert_raw_text(self):
        payload = {
            "text": "# Reporte de API\nContenido de prueba para endpoint de conversión.",
            "custom_title": "Reporte de API",
            "auto_open": False
        }
        status, _, data = self._http_post_json("/api/convert", payload)
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("title"), "Reporte de API")
        self.assertTrue(Path(data.get("file_path")).exists())
        self.assertIn("reporte-de-api", data.get("filename"))

    def test_post_convert_from_physical_file(self):
        md_file = self.create_md_file("sample_test.md", "# Documento desde Archivo\nTexto de prueba.")
        payload = {
            "file_path": str(md_file),
            "auto_open": False
        }
        status, _, data = self._http_post_json("/api/convert", payload)
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("title"), "Documento desde Archivo")
        self.assertTrue(Path(data.get("file_path")).exists())

    def test_post_convert_empty_text_returns_400(self):
        status, _, data = self._http_post_json("/api/convert", {"text": "   "})
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_post_delete_document(self):
        # First convert a document
        res_conv = md_engine.convert_and_update_library("# Documento a Borrar\nContenido.", str(self.test_root))
        created_file = Path(res_conv["file_path"])
        self.assertTrue(created_file.exists())

        # Now delete it via API
        status, _, data = self._http_post_json("/api/delete-document", {
            "filename": res_conv["filename"],
            "file_path": res_conv["file_path"]
        })
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertFalse(created_file.exists(), "Target file must be unlinked from filesystem")

    def test_post_delete_protected_files_returns_400(self):
        # Trying to delete index.html or latest.html directly
        status, _, data = self._http_post_json("/api/delete-document", {"filename": "index.html"})
        self.assertEqual(status, 400)
        self.assertIn("error", data)

        status2, _, data2 = self._http_post_json("/api/delete-document", {"filename": "latest.html"})
        self.assertEqual(status2, 400)

    def test_post_adjust_window(self):
        status, _, data = self._http_post_json("/api/adjust-window", {
            "screen_w": 1920,
            "screen_h": 1080
        })
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("target_w"), 750)
        self.assertEqual(data.get("target_h"), 680)

    def test_post_open_file_and_index(self):
        # open-file with valid url
        status, _, data = self._http_post_json("/api/open-file", {"url": "file:///test.html"})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "opened")

        # open-file without url
        status_err, _, _ = self._http_post_json("/api/open-file", {})
        self.assertEqual(status_err, 400)

        # open-index
        status_idx, _, data_idx = self._http_post_json("/api/open-index")
        self.assertEqual(status_idx, 200)
        self.assertEqual(data_idx.get("status"), "opened")

    def test_post_open_folder(self):
        status, _, data = self._http_post_json("/api/open-folder")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "opened")

    @patch("app.choose_folder_native", return_value="C:/Custom/Folder")
    def test_post_browse_folder_selected(self, mock_dialog):
        # Mock folder dialog
        status, _, data = self._http_post_json("/api/browse-folder")
        self.assertEqual(status, 200)
        self.assertIn("chosen_path", data)

    @patch("app.choose_folder_native", return_value="")
    def test_post_browse_folder_cancelled(self, mock_dialog):
        status, _, data = self._http_post_json("/api/browse-folder")
        self.assertEqual(status, 200)
        self.assertIsNone(data.get("chosen_path"))

    @patch("app.choose_file_native", return_value="C:/Test/doc.md")
    def test_post_browse_file_selected(self, mock_dialog):
        status, _, data = self._http_post_json("/api/browse-file")
        self.assertEqual(status, 200)
        self.assertIn("file_path", data)
        self.assertEqual(data.get("filename"), "doc.md")

    @patch("app.choose_file_native", return_value="")
    def test_post_browse_file_cancelled(self, mock_dialog):
        status, _, data = self._http_post_json("/api/browse-file")
        self.assertEqual(status, 200)
        self.assertIsNone(data.get("file_path"))

    def test_post_shutdown_schedules_shutdown(self):
        status, _, data = self._http_post_json("/api/shutdown", {"delay": 5.0})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "scheduled")
        self.assertEqual(data.get("delay"), 5.0)
        self.assertIsNotNone(app.shutdown_scheduled_time)
        # Cleanup
        app.cancel_scheduled_shutdown()

    def test_incoming_request_cancels_scheduled_shutdown(self):
        app.schedule_shutdown(10.0)
        self.assertIsNotNone(app.shutdown_scheduled_time)

        # A heartbeat should cancel the shutdown
        status, _, data = self._http_post_json("/api/heartbeat")
        self.assertEqual(status, 200)
        self.assertIsNone(app.shutdown_scheduled_time)

        # Test that GET also cancels scheduled shutdown
        app.schedule_shutdown(10.0)
        self.assertIsNotNone(app.shutdown_scheduled_time)
        status_get, _, _ = self._http_get("/api/config")
        self.assertEqual(status_get, 200)
        self.assertIsNone(app.shutdown_scheduled_time)

    def test_is_app_window_alive_lifecycle(self):
        # Save previous state
        orig_hwnds = app.tracked_app_hwnds.copy()
        orig_detected = app.initial_window_detected

        try:
            # Case 1: Tracked HWND is valid in OS
            app.tracked_app_hwnds = {12345}
            app.initial_window_detected = True
            with patch("ctypes.windll.user32.IsWindow", return_value=1):
                self.assertTrue(app.is_app_window_alive())

            # Case 2: Tracked HWND was closed/destroyed by user
            with patch("ctypes.windll.user32.IsWindow", return_value=0), \
                 patch("app.find_app_hwnds", return_value=[]):
                self.assertFalse(app.is_app_window_alive())

            # Case 3: Discovery finds a new window
            app.tracked_app_hwnds = set()
            app.initial_window_detected = False
            with patch("app.find_app_hwnds", return_value=[99999]), \
                 patch("ctypes.windll.user32.IsWindow", return_value=1):
                self.assertTrue(app.is_app_window_alive())
                self.assertIn(99999, app.tracked_app_hwnds)
        finally:
            app.tracked_app_hwnds = orig_hwnds
            app.initial_window_detected = orig_detected

    def test_get_logs(self):
        status, headers, body = self._http_get("/api/logs")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        data = json.loads(body.decode("utf-8"))
        self.assertIn("logs", data)
        self.assertIsInstance(data["logs"], list)

    def test_open_logs(self):
        with patch("os.startfile") as mock_startfile:
            status, _, data = self._http_post_json("/api/open-logs")
            self.assertEqual(status, 200)
            self.assertEqual(data.get("status"), "opened")
            mock_startfile.assert_called_once()

    def test_get_clipboard_endpoint(self):
        sample = "# Markdown desde portapapeles\n- Tarea 1"
        with patch("app.get_clipboard_text", return_value=sample):
            status, headers, body = self._http_get("/api/clipboard")
            self.assertEqual(status, 200)
            self.assertIn("application/json", headers.get("Content-Type", ""))
            data = json.loads(body.decode("utf-8"))
            self.assertEqual(data.get("text"), sample)
            self.assertEqual(data.get("length"), len(sample))

    def test_post_clipboard_endpoint(self):
        sample = "Contenido vía POST"
        with patch("app.get_clipboard_text", return_value=sample):
            status, _, data = self._http_post_json("/api/clipboard")
            self.assertEqual(status, 200)
            self.assertEqual(data.get("text"), sample)
            self.assertEqual(data.get("length"), len(sample))

    def test_get_server_port_preferred_and_fallback(self):
        # 1. Con un puerto libre
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            free_p = s.getsockname()[1]

        chosen = app.get_server_port(preferred_port=free_p)
        self.assertEqual(chosen, free_p)

        # 2. Con un puerto ocupado (bloqueado por un socket activo)
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(('127.0.0.1', 0))
        busy_p = blocker.getsockname()[1]
        try:
            fallback = app.get_server_port(preferred_port=busy_p)
            self.assertNotEqual(fallback, busy_p)
            self.assertGreater(fallback, 0)
        finally:
            blocker.close()

    def test_get_clipboard_text_defensive_behavior(self):
        # Cuando OpenClipboard falla
        with patch("ctypes.windll.user32.OpenClipboard", return_value=0):
            res = app.get_clipboard_text()
            self.assertEqual(res, "")

    def test_post_open_app_endpoint(self):
        with patch("app.open_app_window") as mock_open:
            status, _, data = self._http_post_json("/api/open-app")
            self.assertEqual(status, 200)
            self.assertEqual(data.get("status"), "opened")
            mock_open.assert_called_once()

    def test_post_quit_app_endpoint(self):
        try:
            status, _, data = self._http_post_json("/api/quit-app")
            self.assertEqual(status, 200)
            self.assertEqual(data.get("status"), "quitting")
            self.assertIsNotNone(app.shutdown_scheduled_time)
        finally:
            app.cancel_scheduled_shutdown()

    def test_post_shutdown_with_window_unload_preserves_tray(self):
        # When system_tray_enabled and close_to_tray are true
        cfg = app.get_or_create_config()
        cfg["system_tray_enabled"] = True
        cfg["close_to_tray"] = True
        app.save_config(cfg)

        status, _, data = self._http_post_json("/api/shutdown", {"reason": "window_unload"})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "tray_preserved")
        self.assertIsNone(app.shutdown_scheduled_time)

    def test_post_config_updates_tray_settings(self):
        status, _, data = self._http_post_json("/api/config", {
            "system_tray_enabled": False,
            "close_to_tray": False
        })
        self.assertEqual(status, 200)
        self.assertFalse(data.get("system_tray_enabled"))
        self.assertFalse(data.get("close_to_tray"))


if __name__ == "__main__":
    unittest.main()


