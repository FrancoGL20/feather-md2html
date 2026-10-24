#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper utilities and base classes for MarkdownToHTML test suite.
Ensures zero pollution of host files or user directories during testing.
"""

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure app directory is in sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app
import md_engine


class IsolatedEnvironmentTestCase(unittest.TestCase):
    """
    Base test case that creates a completely isolated temporary environment.
    Redirects config.json and root library directory to temporary storage.
    """

    def setUp(self):
        super().setUp()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="md2html_test_"))
        self.test_root = self.temp_dir / "library"
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.test_config = self.temp_dir / "config.json"

        # Backup original app paths
        self._orig_config_file = app.CONFIG_FILE
        self._orig_default_root = app.DEFAULT_ROOT_DIR

        # Patch app module variables
        app.CONFIG_FILE = self.test_config
        app.DEFAULT_ROOT_DIR = self.test_root

        # Prevent browser and OS popups
        self.browser_patcher = patch("webbrowser.open", return_value=True)
        self.mock_browser = self.browser_patcher.start()

        self.startfile_patcher = patch("os.startfile", return_value=True, create=True)
        self.mock_startfile = self.startfile_patcher.start()

    def tearDown(self):
        # Stop patchers
        self.browser_patcher.stop()
        self.startfile_patcher.stop()

        # Restore original paths
        app.CONFIG_FILE = self._orig_config_file
        app.DEFAULT_ROOT_DIR = self._orig_default_root

        # Remove temporary directories
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        super().tearDown()

    def create_md_file(self, filename: str, content: str) -> Path:
        """Helper to create a temporary markdown file."""
        file_path = self.temp_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path
