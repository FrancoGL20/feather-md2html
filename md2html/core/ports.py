#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hexagonal Architecture Ports (Interfaces).
Defines structural contracts using typing.Protocol so core use cases remain
decoupled from filesystem, HTTP, and Windows OS implementations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple


class ConfigRepositoryPort(Protocol):
    """Port for loading and persisting application configuration and conversion history."""

    def get_or_create_config(self) -> Dict[str, Any]:
        ...

    def save_config(self, config: Dict[str, Any]) -> None:
        ...

    def add_recent_conversion(self, doc_info: Dict[str, Any]) -> None:
        ...


class CatalogCachePort(Protocol):
    """Port for managing document title metadata caching to prevent unnecessary disk reads."""

    def load_cache(self, root_dir: Path) -> Dict[str, Any]:
        ...

    def save_cache(self, root_dir: Path, cache: Dict[str, Any]) -> None:
        ...

    def remove_entry(self, root_dir: Path, filename: str) -> None:
        ...

    def get_title_or_read(self, file_path: Path, known_title: Optional[str] = None) -> str:
        ...


class WindowManagerPort(Protocol):
    """Port for OS window discovery, lifecycle verification, and DPI-aware geometry adjustment."""

    def find_app_hwnds(self) -> List[int]:
        ...

    def calculate_geometry(
        self, screen_w: Optional[int] = None, screen_h: Optional[int] = None
    ) -> Tuple[int, int, int, int]:
        ...

    def adjust_window(
        self,
        target_w: int,
        target_h: int,
        pos_x: Optional[int] = None,
        pos_y: Optional[int] = None,
        retries: int = 25,
    ) -> bool:
        ...


class ClipboardPort(Protocol):
    """Port for native system clipboard access."""

    def get_text(self) -> str:
        ...


class NativeDialogPort(Protocol):
    """Port for native OS file and directory selection dialogs."""

    def choose_folder(self, initial_dir: str = "") -> str:
        ...

    def choose_file(self) -> str:
        ...
