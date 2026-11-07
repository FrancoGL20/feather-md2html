#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hierarchical document title detection from custom input, YAML frontmatter,
Markdown headings (ATX and Setext), filename stems, or initial text lines.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from md2html.core.compiler.ast_nodes import is_list_marker
from md2html.core.compiler.inline_parser import clean_markdown_inline
from md2html.core.compiler.math_protector import (
    _TOKEN_BLOCK_PREFIX,
    _TOKEN_INLINE_PREFIX,
    is_math_heading_or_line,
)

_GENERIC_FILE_STEMS = frozenset(
    {"temp", "input", "a", "b", "test", "tmp", "untitled", "document", "documento"}
)


def find_code_block_line_indices(lines: List[str]) -> set:
    """
    Identifies all line indices that are inside (or are the fences of)
    fenced code blocks (``` or ~~~).
    """
    code_indices = set()
    in_code = False
    fence_char = ""
    fence_len = 0

    for idx, line in enumerate(lines):
        st = line.strip()
        if not in_code:
            m = re.match(r"^(`{3,}|~{3,})", st)
            if m:
                in_code = True
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                code_indices.add(idx)
        else:
            code_indices.add(idx)
            m = re.match(r"^(`{3,}|~{3,})\s*$", st)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                in_code = False

    return code_indices


def format_stem_as_title(stem: str) -> str:
    """Converts a filename stem into a human-readable title, stripping date suffixes."""
    stem = re.sub(r"_\d{8}_\d{6}$", "", stem)
    stem = re.sub(r"_\d{8}$", "", stem)
    title = re.sub(r"[-_]+", " ", stem).strip()
    words = [w.capitalize() if not w.isupper() else w for w in title.split()]
    return " ".join(words)


def detect_smart_title(
    lines: List[str],
    custom_title: Optional[str] = None,
    input_file_path: Optional[str] = None,
    frontmatter: Optional[Dict[str, str]] = None,
) -> Tuple[str, str, int]:
    """
    Detects the most representative title for a Markdown document.

    Returns:
        Tuple of (title, title_source, title_line_index).
    """
    if custom_title and custom_title.strip():
        return clean_markdown_inline(custom_title.strip()), "custom", -1

    if frontmatter:
        for k in ("title", "name", "subject", "topic", "titulo", "heading"):
            val = frontmatter.get(k)
            if val and str(val).strip():
                return clean_markdown_inline(str(val).strip()), "frontmatter", -1

    n = len(lines)
    code_indices = find_code_block_line_indices(lines)

    # Priority 3: Explicit H1 (# or Setext ===)
    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        st = l.strip()
        m_h1 = re.match(r"^[ ]{0,3}#\s+(.+)$", l)
        if m_h1:
            cl = clean_markdown_inline(m_h1.group(1))
            if cl:
                return cl, "h1", idx
        if idx + 1 < n and st and not st.startswith(("#", "```", "~~~", ">", "|", "- ", "* ", "+ ")):
            if (idx + 1) not in code_indices and re.match(r"^[=]{3,}\s*$", lines[idx + 1].strip()):
                cl = clean_markdown_inline(st)
                if cl:
                    return cl, "setext_h1", idx

    # Priority 4: H2 (## or Setext ---) or H3 (###) down to H6 (######) when no H1 is present
    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        st = l.strip()
        m_h2 = re.match(r"^[ ]{0,3}##\s+(.+)$", l)
        if m_h2:
            cl = clean_markdown_inline(m_h2.group(1))
            if cl:
                return cl, "h2", idx
        if idx + 1 < n and st and not st.startswith(("#", "```", "~~~", ">", "|", "- ", "* ", "+ ", "---")):
            if (idx + 1) not in code_indices and re.match(r"^[-]{3,}\s*$", lines[idx + 1].strip()):
                cl = clean_markdown_inline(st)
                if cl:
                    return cl, "setext_h2", idx

    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        st = l.strip()
        m_h3 = re.match(r"^[ ]{0,3}###\s+(.+)$", l)
        if m_h3:
            cl = clean_markdown_inline(m_h3.group(1))
            if cl:
                return cl, "h3", idx

    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        st = l.strip()
        m_h4 = re.match(r"^[ ]{0,3}####\s+(.+)$", l)
        if m_h4:
            cl = clean_markdown_inline(m_h4.group(1))
            if cl:
                return cl, "h4", idx

    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        st = l.strip()
        m_h5 = re.match(r"^[ ]{0,3}#####\s+(.+)$", l)
        if m_h5:
            cl = clean_markdown_inline(m_h5.group(1))
            if cl:
                return cl, "h5", idx

    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        st = l.strip()
        m_h6 = re.match(r"^[ ]{0,3}######\s+(.+)$", l)
        if m_h6:
            cl = clean_markdown_inline(m_h6.group(1))
            if cl:
                return cl, "h6", idx

    # Priority 5: Non-generic physical filename stem
    if input_file_path:
        stem = Path(input_file_path).stem
        if stem.lower() not in _GENERIC_FILE_STEMS:
            candidate = format_stem_as_title(stem)
            if candidate:
                return candidate, "file_stem", -1

    # Priority 6: Prominent bold line near the top of the document
    checked_bold_lines = 0
    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        checked_bold_lines += 1
        if checked_bold_lines > 15:
            break
        st = l.strip()
        if (
            not st
            or st.startswith(("#", "```", "~~~", ">", "|", "---", "===", "***", _TOKEN_BLOCK_PREFIX, _TOKEN_INLINE_PREFIX))
            or is_math_heading_or_line(st)
        ):
            continue
        m_bold = re.match(r"^\s*(\*\*|__)(.*?)\1\s*$", st)
        if m_bold:
            cl = clean_markdown_inline(m_bold.group(2))
            if len(cl) >= 3:
                return cl, "bold_line", idx

    # Priority 7: First meaningful paragraph line (excluding list items)
    checked_para_lines = 0
    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        checked_para_lines += 1
        if checked_para_lines > 20:
            break
        st = l.strip()
        if (
            not st
            or st.startswith(
                ("#", "```", "~~~", ">", "|", "---", "===", "***", "<!--", "<", _TOKEN_BLOCK_PREFIX, _TOKEN_INLINE_PREFIX)
            )
            or is_math_heading_or_line(st)
            or is_list_marker(l)
        ):
            continue
        if _TOKEN_INLINE_PREFIX in st:
            continue
        cl = clean_markdown_inline(st)
        if len(cl) >= 4:
            if len(cl) > 70:
                truncated = cl[:70].rsplit(" ", 1)[0]
                cl = f"{truncated}..."
            return cl, "first_line", idx

    # Priority 8: First list item if document contains lists without paragraphs
    checked_list_lines = 0
    for idx, l in enumerate(lines):
        if idx in code_indices:
            continue
        checked_list_lines += 1
        if checked_list_lines > 20:
            break
        st = l.strip()
        if is_list_marker(l):
            cl = clean_markdown_inline(st)
            if len(cl) >= 4:
                if len(cl) > 70:
                    truncated = cl[:70].rsplit(" ", 1)[0]
                    cl = f"{truncated}..."
                return cl, "list_item", idx

    now_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    return f"Documento Markdown ({now_str})", "fallback", -1
