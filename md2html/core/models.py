#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core domain models and value objects.
Uses Python standard library dataclasses with dictionary-access compatibility
so both typed services and dictionary-based callers operate seamlessly.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterator, List, Optional


class _DictCompatibleMixin:
    """Provides mapping-style read access (__getitem__, get, keys, __contains__) on dataclasses."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def keys(self) -> Iterator[str]:
        return iter(self.__dataclass_fields__.keys())


@dataclass
class ParsedDocument(_DictCompatibleMixin):
    """Represents the output of the Markdown lexical/syntactic compiler."""

    title: str
    body: str
    toc: str = ""
    badge: str = ""
    subtitle: str = ""
    frontmatter: Dict[str, str] = field(default_factory=dict)
    has_mermaid: bool = False
    has_math: bool = False


@dataclass
class ConversionResult(_DictCompatibleMixin):
    """Represents the result of compiling a document and updating the library catalog."""

    success: bool
    file_path: str
    file_url: str
    filename: str
    title: str
    index_path: str = ""
    index_url: str = ""
    latest_url: str = ""
    words: int = 0
    reading_time: Any = ""
    root_dir: str = ""
    timestamp: str = ""


@dataclass(frozen=True)
class WindowGeometry:
    """Calculated native window dimensions and screen coordinates."""

    width: int
    height: int
    pos_x: int
    pos_y: int

    def as_tuple(self) -> tuple:
        return (self.width, self.height, self.pos_x, self.pos_y)

    def __iter__(self) -> Iterator[int]:
        return iter((self.width, self.height, self.pos_x, self.pos_y))
