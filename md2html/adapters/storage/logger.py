#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thread-safe rotating file logger for background server diagnostics."""

import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_FILE = PROJECT_ROOT / "debug_log.txt"

_log_lock = threading.Lock()


def log_debug(msg: str, log_file: Optional[Path] = None) -> None:
    """Appends a timestamped entry to debug_log.txt with automatic 1 MB size rotation."""
    target = log_file or DEFAULT_LOG_FILE
    try:
        with _log_lock:
            if target.exists() and target.stat().st_size > 1_000_000:
                try:
                    with open(target, "r", encoding="utf-8", errors="ignore") as rf:
                        rf.seek(max(0, target.stat().st_size - 250_000))
                        tail = rf.read()
                    with open(target, "w", encoding="utf-8") as wf:
                        wf.write(f"--- [REGISTRO ROTADO] ---\n{tail}")
                except Exception:
                    pass
            with open(target, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}\n")
    except Exception:
        pass


def read_recent_logs(log_file: Optional[Path] = None, max_lines: int = 80) -> List[str]:
    """Reads the last max_lines lines from debug_log.txt."""
    target = log_file or DEFAULT_LOG_FILE
    if not target.exists():
        return []
    try:
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            return [line.rstrip() for line in f.readlines()[-max_lines:]]
    except Exception:
        return []
