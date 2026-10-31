#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template and offline runtime loader with in-memory caching.
Loads CSS stylesheets, HTML templates, and offline JS bundles (Mermaid, MathJax)
once from disk and serves them from RAM for sub-millisecond injection.
"""

from pathlib import Path
from typing import Dict, Optional

TEMPLATES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEMPLATES_DIR.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

_FILE_CACHE: Dict[str, str] = {}
_mermaid_js_cache: Optional[str] = None
_mathjax_js_cache: Optional[str] = None


def _read_template_file(rel_path: str) -> str:
    """Reads and caches a template resource relative to TEMPLATES_DIR."""
    if rel_path in _FILE_CACHE:
        return _FILE_CACHE[rel_path]
    target = TEMPLATES_DIR / rel_path
    content = target.read_text(encoding="utf-8")
    _FILE_CACHE[rel_path] = content
    return content


def get_math_styles() -> str:
    """Returns CSS styles for MathJax SVG containers."""
    return "\n" + _read_template_file("styles/math.css")


def get_common_styles() -> str:
    """Returns combined base document CSS and MathJax CSS."""
    doc_css = _read_template_file("styles/document.css")
    math_css = get_math_styles()
    return "\n" + doc_css + math_css


def get_catalog_styles() -> str:
    """Returns CSS specific to the library catalog (index.html)."""
    return _read_template_file("styles/catalog.css")


def get_mermaid_client_js() -> str:
    """Returns client-side JS controller for interactive Mermaid blocks."""
    return "\n" + _read_template_file("scripts/mermaid_client.js")


def get_html_doc_template() -> str:
    """Returns the standalone HTML document template."""
    return _read_template_file("html/document.html")


def get_catalog_template() -> str:
    """Returns the library index.html template."""
    return _read_template_file("html/catalog.html")


def get_latest_redirect_template() -> str:
    """Returns the latest.html redirect page template."""
    return _read_template_file("html/latest_redirect.html")


def get_mermaid_runtime_code() -> str:
    """
    Loads the minified Mermaid 11.x runtime from assets/ offline.
    Caches the bundle in memory for sub-millisecond subsequent reads.
    """
    global _mermaid_js_cache
    if _mermaid_js_cache is not None:
        return _mermaid_js_cache

    candidates = [
        ASSETS_DIR / "mermaid.min.js",
        Path.home() / ".gemini" / "config" / "skills" / "markdown-to-html" / "references" / "mermaid.min.js",
    ]
    for cand in candidates:
        if cand.exists():
            try:
                _mermaid_js_cache = cand.read_text(encoding="utf-8")
                return _mermaid_js_cache
            except Exception:
                pass
    return ""


def get_math_runtime_code() -> str:
    """
    Loads the minified MathJax 3 (tex-svg) runtime from assets/ offline.
    Caches the bundle in memory for sub-millisecond subsequent reads.
    """
    global _mathjax_js_cache
    if _mathjax_js_cache is not None:
        return _mathjax_js_cache

    candidates = [
        ASSETS_DIR / "tex-svg.min.js",
        Path.home() / ".gemini" / "config" / "skills" / "markdown-to-html" / "references" / "tex-svg.min.js",
    ]
    for cand in candidates:
        if cand.exists():
            try:
                _mathjax_js_cache = cand.read_text(encoding="utf-8")
                return _mathjax_js_cache
            except Exception:
                pass
    return ""
