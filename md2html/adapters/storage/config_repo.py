#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON configuration repository and conversion history synchronization adapter.
Manages config.json persistence, template initialization, ghost file pruning,
and automatic discovery of pre-existing HTML documents in the library root.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from md2html.adapters.storage.index_cache import extract_title_from_html

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config.json"
DEFAULT_TEMPLATE_FILE = PROJECT_ROOT / "config.template.json"
DEFAULT_LIBRARY_ROOT = Path.home() / "Downloads" / "Markdown_HTML_Library"


class JsonConfigRepository:
    """Manages reading, validating, and saving application configuration."""

    def __init__(
        self,
        config_file_getter: Callable[[], Path],
        template_file_getter: Callable[[], Path],
        default_root_getter: Callable[[], Path],
        index_generator: Optional[Callable[[Path], Any]] = None,
    ) -> None:
        self._get_config_file = config_file_getter
        self._get_template_file = template_file_getter
        self._get_default_root = default_root_getter
        self._index_generator = index_generator

    def get_or_create_config(self) -> Dict[str, Any]:
        """Loads config.json, initializes from template if absent, and synchronizes disk history."""
        config_file = self._get_config_file()
        template_file = self._get_template_file()
        default_root = self._get_default_root()

        config: Dict[str, Any] = {
            "root_dir": str(default_root),
            "auto_open": True,
            "system_tray_enabled": True,
            "close_to_tray": True,
            "first_tray_notification_shown": False,
            "recent_conversions": [],
        }

        if not config_file.exists() and template_file.exists():
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                    config.update(template_data)
            except Exception:
                pass

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config.update(loaded)
            except Exception as e:
                print(f"Aviso: Error leyendo config.json, usando valores predeterminados: {e}")

        root_path = Path(config.get("root_dir") or default_root)
        try:
            root_path.mkdir(parents=True, exist_ok=True)
            config["root_dir"] = str(root_path.resolve())
        except Exception as e:
            print(f"Error verificando ruta raíz '{root_path}', recurriendo a default: {e}")
            default_root.mkdir(parents=True, exist_ok=True)
            config["root_dir"] = str(default_root.resolve())
            root_path = default_root

        # Prune ghost entries whose physical HTML files no longer exist on disk
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

        # Discover untracked HTML documents in root_dir (sorted newest first, capped at 10)
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
                candidates.sort(key=lambda x: x[1], reverse=True)
                for f, mtime in candidates[:10]:
                    try:
                        dt = datetime.fromtimestamp(mtime)
                        doc_title = extract_title_from_html(f)
                        untracked_items.append(
                            {
                                "item": {
                                    "title": doc_title,
                                    "filename": f.name,
                                    "file_url": f"file:///{f.resolve().as_posix()}",
                                    "file_path": str(f.resolve()),
                                    "timestamp": dt.strftime("%d/%m/%Y %I:%M %p"),
                                },
                                "mtime": mtime,
                            }
                        )
                    except Exception:
                        continue

        if untracked_items:
            untracked_items.sort(key=lambda x: x["mtime"], reverse=True)
            untracked_list = [entry["item"] for entry in untracked_items]
            if not valid_recents:
                valid_recents = untracked_list
            else:
                valid_recents.extend(untracked_list)

        config["recent_conversions"] = valid_recents[:10]
        self.save_config(config)

        if self._index_generator:
            try:
                self._index_generator(root_path)
            except Exception:
                pass

        return config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Persists the configuration dictionary to config.json."""
        config_file = self._get_config_file()
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando config.json: {e}")

    def add_recent_conversion(self, doc_info: Dict[str, Any]) -> None:
        """Prepends a converted document to recent_conversions without duplicates (max 10)."""
        config = self.get_or_create_config()
        recents = config.get("recent_conversions", [])
        recents = [r for r in recents if r.get("filename") != doc_info.get("filename")]
        recents.insert(
            0,
            {
                "title": doc_info.get("title"),
                "filename": doc_info.get("filename"),
                "file_url": doc_info.get("file_url"),
                "file_path": doc_info.get("file_path"),
                "timestamp": doc_info.get("timestamp"),
            },
        )
        config["recent_conversions"] = recents[:10]
        self.save_config(config)
