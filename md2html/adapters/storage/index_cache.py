#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document title metadata caching adapter.
Persists a lightweight .index_cache.json keyed by (filename, mtime, size_kb)
to avoid reopening large HTML bundles and triggering heuristic AV scans.
"""

import json
import re
import threading
from pathlib import Path
from typing import Any, Dict, Optional

_INDEX_CACHE_LOCK = threading.Lock()
_TITLE_CACHE: Dict[str, Dict[str, Any]] = {}


def load_index_cache(root_dir: Path) -> Dict[str, Any]:
    """Loads .index_cache.json from root_dir if present and valid."""
    cache_file = root_dir / ".index_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_index_cache(root_dir: Path, cache: Dict[str, Any]) -> None:
    """Writes .index_cache.json defensively to root_dir."""
    cache_file = root_dir / ".index_cache.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass


def remove_from_index_cache(root_dir: Path, filename: str) -> None:
    """Removes a deleted document's entry from both disk and in-memory title caches."""
    cache = load_index_cache(root_dir)
    if filename in cache:
        del cache[filename]
        save_index_cache(root_dir, cache)
    with _INDEX_CACHE_LOCK:
        for k in list(_TITLE_CACHE.keys()):
            if k.endswith(filename) or k.endswith(f"\\{filename}") or k.endswith(f"/{filename}"):
                _TITLE_CACHE.pop(k, None)


def get_cached_title_or_read(file_path: Path, known_title: Optional[str] = None) -> str:
    """
    Retrieves the document title from in-memory or disk cache by (mtime, size_kb).
    Falls back to reading only the first 4,000 bytes of the HTML file on cache miss.
    """
    try:
        resolved_str = str(file_path.resolve())
        stat = file_path.stat()
        mtime = stat.st_mtime
        size_kb = max(1, round(stat.st_size / 1024))
    except Exception:
        resolved_str = str(file_path)
        mtime = 0
        size_kb = 0

    if known_title:
        with _INDEX_CACHE_LOCK:
            _TITLE_CACHE[resolved_str] = {
                "title": known_title,
                "mtime": mtime,
                "size_kb": size_kb,
            }
        return known_title

    with _INDEX_CACHE_LOCK:
        cached = _TITLE_CACHE.get(resolved_str)
        if cached and cached.get("mtime") == mtime and cached.get("size_kb") == size_kb:
            return cached["title"]

    try:
        p_cache = load_index_cache(file_path.parent)
        if file_path.name in p_cache:
            entry = p_cache[file_path.name]
            if entry.get("mtime") == mtime and entry.get("size_kb") == size_kb:
                doc_title = entry["title"]
                with _INDEX_CACHE_LOCK:
                    _TITLE_CACHE[resolved_str] = {
                        "title": doc_title,
                        "mtime": mtime,
                        "size_kb": size_kb,
                    }
                return doc_title
    except Exception:
        pass

    fallback = file_path.stem.replace("-", " ").replace("_", " ").capitalize()
    doc_title = fallback
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            head_chunk = fh.read(4000)
            t_match = re.search(r"<title>(.*?)</title>", head_chunk, re.IGNORECASE)
            if t_match and t_match.group(1).strip():
                doc_title = t_match.group(1).strip()
    except Exception:
        pass

    with _INDEX_CACHE_LOCK:
        _TITLE_CACHE[resolved_str] = {
            "title": doc_title,
            "mtime": mtime,
            "size_kb": size_kb,
        }
    return doc_title


def extract_title_from_html(file_path: Path) -> str:
    """Extracts the title of an HTML document using cache or <title> tag fallback."""
    try:
        return get_cached_title_or_read(file_path)
    except Exception:
        return file_path.stem.replace("-", " ").replace("_", " ").capitalize()
