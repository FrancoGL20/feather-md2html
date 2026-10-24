#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security and Defensive Architecture Tests (tests/test_security.py).
Tests directory traversal prevention, forbidden file deletion protection,
and XSS escaping in Markdown compilation and API endpoints.
"""

import sys
import unittest
import urllib.request
import urllib.error
import threading
from http.server import HTTPServer
from pathlib import Path

# Add app directory to sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app
import md_engine
from tests.test_helpers import IsolatedEnvironmentTestCase


class TestSecurityDefenses(IsolatedEnvironmentTestCase):
    """Test security boundaries, traversal protections, and injection sanitization."""

    def setUp(self):
        super().setUp()
        self.server = HTTPServer(('127.0.0.1', 0), app.AppRequestHandler)
        self.port = self.server.server_port
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)
        super().tearDown()

    def test_asset_directory_traversal_blocked(self):
        """Prevent path traversal like /assets/../config.json from serving unauthorized files."""
        traversal_paths = [
            "/assets/../config.json",
            "/assets/../../app.py",
            "/assets/..%2f..%2fconfig.json"
        ]
        for t_path in traversal_paths:
            url = f"{self.base_url}{t_path}"
            req = urllib.request.Request(url, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=3) as resp:
                    # If it somehow returns 200, ensure it did NOT return config content
                    body = resp.read().decode("utf-8", errors="ignore")
                    self.assertNotIn("root_dir", body)
            except urllib.error.HTTPError as e:
                # 404 is the expected defensive response
                self.assertEqual(e.code, 404)
                e.close()

    def test_delete_arbitrary_system_file_blocked(self):
        """Ensure delete-document cannot delete non-HTML or external sensitive files."""
        secret_file = self.temp_dir / "secret_keys.txt"
        secret_file.write_text("SUPER_SECRET_KEY=12345", encoding="utf-8")

        # Attempt to delete via file_path
        status, _, data = self._post_delete({
            "file_path": str(secret_file),
            "filename": "secret_keys.txt"
        })
        self.assertEqual(status, 400, "Non-html files must be rejected")
        self.assertTrue(secret_file.exists(), "Secret file must remain untouched")

    def test_delete_protected_index_and_latest_blocked(self):
        """Ensure index.html and latest.html are immune to deletion."""
        index_file = self.test_root / "index.html"
        index_file.write_text("<h1>Index</h1>", encoding="utf-8")

        status, _, _ = self._post_delete({"filename": "index.html"})
        self.assertEqual(status, 400)
        self.assertTrue(index_file.exists())

        status2, _, _ = self._post_delete({"filename": "latest.html"})
        self.assertEqual(status2, 400)

    def test_xss_script_tags_escaped_in_code_blocks(self):
        """Ensure script tags inside code blocks are HTML-escaped and non-executable."""
        md = "```html\n<script>alert('xss');</script>\n```"
        compiled = md_engine.compile_markdown_to_body(md)
        self.assertNotIn("<script>", compiled)
        self.assertIn("&lt;script&gt;alert('xss');&lt;/script&gt;", compiled)

    def test_xss_script_tags_escaped_in_inline_code(self):
        """Ensure script tags in inline code are HTML-escaped."""
        md = "# Encabezado Principal\n\nEjemplo con `<script>alert(document.cookie);</script>` en el texto."
        compiled = md_engine.compile_markdown_to_body(md)
        self.assertNotIn("<script>", compiled)
        self.assertIn("&lt;script&gt;alert(document.cookie);&lt;/script&gt;", compiled)

    def _post_delete(self, payload: dict):
        import json
        url = f"{self.base_url}/api/delete-document"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return resp.status, dict(resp.headers), data
        except urllib.error.HTTPError as e:
            try:
                data = json.loads(e.read().decode("utf-8"))
                return e.code, dict(e.headers), data
            finally:
                e.close()


if __name__ == "__main__":
    unittest.main()
