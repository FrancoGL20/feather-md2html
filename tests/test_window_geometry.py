#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Window Geometry and Responsive Window Sizing (app.py).
Tests resolution detection, screen size adaptation, centering mathematics, and boundary clamps.
"""

import sys
import unittest
from pathlib import Path

# Add app directory to sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app


class TestWindowGeometry(unittest.TestCase):
    """Test get_dynamic_window_geometry calculations for different display profiles."""

    def test_large_desktop_1080p(self):
        # 1920 x 1080
        tw, th, px, py = app.get_dynamic_window_geometry(1920, 1080)
        self.assertEqual(tw, 750, "Desktop width should be compact (750px)")
        self.assertEqual(th, 680, "Desktop height capped at 680px")
        self.assertEqual(px, (1920 - 750) // 2, "X coordinate should be horizontally centered")
        self.assertEqual(py, (1080 - 680) // 2, "Y coordinate should be vertically centered")

    def test_large_desktop_2k_and_4k(self):
        # 2560 x 1440 (2K)
        tw_2k, th_2k, px_2k, py_2k = app.get_dynamic_window_geometry(2560, 1440)
        self.assertEqual(tw_2k, 750)
        self.assertEqual(th_2k, 680)
        self.assertEqual(px_2k, (2560 - 750) // 2)
        self.assertEqual(py_2k, (1440 - 680) // 2)

        # 3840 x 2160 (4K)
        tw_4k, th_4k, px_4k, py_4k = app.get_dynamic_window_geometry(3840, 2160)
        self.assertEqual(tw_4k, 750)
        self.assertEqual(th_4k, 680)
        self.assertEqual(px_4k, (3840 - 750) // 2)
        self.assertEqual(py_4k, (2160 - 680) // 2)

    def test_laptop_standard_1366x768(self):
        # 1366 x 768 (< 1600px width)
        tw, th, px, py = app.get_dynamic_window_geometry(1366, 768)
        expected_w = int(1366 * 0.85)
        expected_h = int(768 * 0.86)
        self.assertEqual(tw, expected_w, "Laptop width should be ~85% of display width")
        self.assertEqual(th, expected_h, "Laptop height should be ~86% of display height")
        self.assertEqual(px, (1366 - expected_w) // 2)
        self.assertEqual(py, (768 - expected_h) // 2)

    def test_laptop_1280x720(self):
        # 1280 x 720
        tw, th, px, py = app.get_dynamic_window_geometry(1280, 720)
        expected_w = int(1280 * 0.85)
        expected_h = int(720 * 0.86)
        self.assertEqual(tw, expected_w)
        self.assertEqual(th, expected_h)
        self.assertEqual(px, (1280 - expected_w) // 2)
        self.assertEqual(py, (720 - expected_h) // 2)

    def test_laptop_1440x900(self):
        # 1440 x 900
        tw, th, px, py = app.get_dynamic_window_geometry(1440, 900)
        expected_w = int(1440 * 0.85)
        # Height capped by min(760, int(900 * 0.86) = 774) -> 760
        expected_h = 760
        self.assertEqual(tw, expected_w)
        self.assertEqual(th, expected_h)
        self.assertEqual(px, (1440 - expected_w) // 2)
        self.assertEqual(py, (900 - expected_h) // 2)

    def test_minimum_dimension_clamping(self):
        # Ultra-low resolution (800 x 600)
        tw, th, px, py = app.get_dynamic_window_geometry(800, 600)
        self.assertGreaterEqual(tw, 680, "Width should never be smaller than 680px")
        self.assertGreaterEqual(th, 560, "Height should never be smaller than 560px")
        self.assertGreaterEqual(px, 0, "Position X should never be negative")
        self.assertGreaterEqual(py, 0, "Position Y should never be negative")

    def test_boundary_and_invalid_inputs(self):
        # String inputs that can be converted
        tw, th, px, py = app.get_dynamic_window_geometry("1920", "1080")
        self.assertEqual(tw, 750)
        self.assertEqual(th, 680)

        # None inputs fallback safely without crashing
        tw_none, th_none, px_none, py_none = app.get_dynamic_window_geometry(None, None)
        self.assertIsInstance(tw_none, int)
        self.assertIsInstance(th_none, int)
        self.assertGreater(tw_none, 0)
        self.assertGreater(th_none, 0)

        # Invalid strings fallback to 1920x1080
        tw_inv, th_inv, px_inv, py_inv = app.get_dynamic_window_geometry("invalid", "invalid")
        self.assertEqual(tw_inv, 750)
        self.assertEqual(th_inv, 680)


    def test_close_app_window_posts_wm_close(self):
        from unittest.mock import patch
        from md2html.core.services.lifecycle_service import AppLifecycleState
        from md2html.adapters.os_win32.window_manager import close_app_window

        state = AppLifecycleState()
        state.tracked_app_hwnds = {10101}

        with patch("ctypes.windll.user32.IsWindow", return_value=1) as mock_is_window, \
             patch("ctypes.windll.user32.PostMessageW", return_value=1) as mock_post:
            result = close_app_window(state)
            self.assertTrue(result)
            mock_is_window.assert_called_with(10101)
            mock_post.assert_called_once_with(10101, 0x0010, 0, 0)

    def test_close_app_window_no_hwnds_returns_false(self):
        from md2html.core.services.lifecycle_service import AppLifecycleState
        from md2html.adapters.os_win32.window_manager import close_app_window

        state = AppLifecycleState()
        state.tracked_app_hwnds = set()
        result = close_app_window(state, find_hwnds_fn=lambda: [])
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
