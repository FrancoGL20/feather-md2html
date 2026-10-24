#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for configuration persistence, defaults, and conversion history (app.py).
Tests config serialization, corruption recovery, history deduplication,
the 10-item limit, and automatic pruning of ghost files.
"""

import sys
import json
import unittest
from pathlib import Path

# Add app directory to sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app
from tests.test_helpers import IsolatedEnvironmentTestCase


class TestConfigAndHistory(IsolatedEnvironmentTestCase):
    """Test configuration lifecycle and recent conversion history."""

    def test_default_config_creation_when_missing(self):
        self.assertFalse(self.test_config.exists())
        config = app.get_or_create_config()

        self.assertTrue(self.test_config.exists())
        self.assertIn("root_dir", config)
        self.assertTrue(config["auto_open"])
        self.assertEqual(config["recent_conversions"], [])

    def test_corrupted_config_recovery(self):
        # Write corrupted JSON
        self.test_config.write_text("{ this is not valid json : [", encoding="utf-8")
        
        # Should gracefully recover and return valid configuration
        config = app.get_or_create_config()
        self.assertIn("root_dir", config)
        self.assertIsInstance(config["recent_conversions"], list)

    def test_add_recent_conversion_basic(self):
        # Create a real test file on disk
        doc_file = self.test_root / "report.html"
        doc_file.write_text("<h1>Report</h1>", encoding="utf-8")

        info = {
            "title": "Reporte de Prueba",
            "filename": "report.html",
            "file_url": f"file:///{doc_file.resolve().as_posix()}",
            "file_path": str(doc_file),
            "timestamp": "23/10/2026 05:00 PM"
        }
        app.add_recent_conversion(info)

        cfg = app.get_or_create_config()
        self.assertEqual(len(cfg["recent_conversions"]), 1)
        self.assertEqual(cfg["recent_conversions"][0]["filename"], "report.html")
        self.assertEqual(cfg["recent_conversions"][0]["title"], "Reporte de Prueba")

    def test_deduplication_moves_existing_to_front(self):
        doc1 = self.test_root / "doc1.html"
        doc1.write_text("<h1>Doc 1</h1>", encoding="utf-8")
        doc2 = self.test_root / "doc2.html"
        doc2.write_text("<h1>Doc 2</h1>", encoding="utf-8")

        app.add_recent_conversion({
            "title": "Doc 1", "filename": "doc1.html",
            "file_path": str(doc1), "file_url": "url1", "timestamp": "10:00"
        })
        app.add_recent_conversion({
            "title": "Doc 2", "filename": "doc2.html",
            "file_path": str(doc2), "file_url": "url2", "timestamp": "10:05"
        })

        # Add Doc 1 again with updated timestamp
        app.add_recent_conversion({
            "title": "Doc 1 Actualizado", "filename": "doc1.html",
            "file_path": str(doc1), "file_url": "url1", "timestamp": "10:10"
        })

        cfg = app.get_or_create_config()
        # Should still only have 2 items, and Doc 1 should be at index 0
        self.assertEqual(len(cfg["recent_conversions"]), 2)
        self.assertEqual(cfg["recent_conversions"][0]["filename"], "doc1.html")
        self.assertEqual(cfg["recent_conversions"][0]["title"], "Doc 1 Actualizado")
        self.assertEqual(cfg["recent_conversions"][1]["filename"], "doc2.html")

    def test_maximum_history_limit_of_ten(self):
        # Create 15 physical files and add them
        for i in range(15):
            f = self.test_root / f"doc_{i}.html"
            f.write_text(f"<h1>Doc {i}</h1>", encoding="utf-8")
            app.add_recent_conversion({
                "title": f"Doc {i}",
                "filename": f"doc_{i}.html",
                "file_path": str(f),
                "file_url": f"url_{i}",
                "timestamp": f"10:{i:02d}"
            })

        cfg = app.get_or_create_config()
        self.assertEqual(len(cfg["recent_conversions"]), 10, "History should be strictly capped at 10 items")
        # Most recent should be doc_14
        self.assertEqual(cfg["recent_conversions"][0]["filename"], "doc_14.html")

    def test_automatic_pruning_of_ghost_files(self):
        # Create 2 real files and 1 fake nonexistent file
        f1 = self.test_root / "real_1.html"
        f1.write_text("Content 1", encoding="utf-8")
        f2 = self.test_root / "real_2.html"
        f2.write_text("Content 2", encoding="utf-8")

        ghost_path = self.test_root / "ghost_deleted.html"
        # Notice: we do NOT create ghost_path on disk

        app.add_recent_conversion({
            "title": "Real 1", "filename": "real_1.html",
            "file_path": str(f1), "file_url": "url1", "timestamp": "10:00"
        })
        app.add_recent_conversion({
            "title": "Ghost", "filename": "ghost_deleted.html",
            "file_path": str(ghost_path), "file_url": "url_ghost", "timestamp": "10:05"
        })
        app.add_recent_conversion({
            "title": "Real 2", "filename": "real_2.html",
            "file_path": str(f2), "file_url": "url2", "timestamp": "10:10"
        })

        # Calling get_or_create_config simulates startup verification
        cfg = app.get_or_create_config()
        filenames = [r["filename"] for r in cfg["recent_conversions"]]
        self.assertIn("real_1.html", filenames)
        self.assertIn("real_2.html", filenames)
        self.assertNotIn("ghost_deleted.html", filenames, "Nonexistent physical files must be purged")


if __name__ == "__main__":
    unittest.main()
