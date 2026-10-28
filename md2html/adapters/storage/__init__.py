#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Storage, metadata cache, and diagnostic logging adapters."""

from md2html.adapters.storage.config_repo import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_LIBRARY_ROOT,
    DEFAULT_TEMPLATE_FILE,
    JsonConfigRepository,
)
from md2html.adapters.storage.index_cache import (
    _INDEX_CACHE_LOCK,
    _TITLE_CACHE,
    extract_title_from_html,
    get_cached_title_or_read,
    load_index_cache,
    remove_from_index_cache,
    save_index_cache,
)
from md2html.adapters.storage.logger import (
    DEFAULT_LOG_FILE,
    log_debug,
    read_recent_logs,
)

__all__ = [
    "DEFAULT_CONFIG_FILE",
    "DEFAULT_LIBRARY_ROOT",
    "DEFAULT_LOG_FILE",
    "DEFAULT_TEMPLATE_FILE",
    "JsonConfigRepository",
    "_INDEX_CACHE_LOCK",
    "_TITLE_CACHE",
    "extract_title_from_html",
    "get_cached_title_or_read",
    "load_index_cache",
    "log_debug",
    "read_recent_logs",
    "remove_from_index_cache",
    "save_index_cache",
]
