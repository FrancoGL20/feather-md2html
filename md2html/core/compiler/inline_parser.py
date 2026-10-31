#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inline Markdown formatting, slug generation, status badges, and syntax highlighting.
"""

import html
import re
import unicodedata
from typing import Dict, List


def escape(text: str) -> str:
    """HTML-escapes text while preserving quotes unless needed."""
    return html.escape(text, quote=False)


def slugify(text: str) -> str:
    """Normalizes arbitrary text into a URL-safe and anchor-safe ASCII slug."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    slug = re.sub(r"[-\s]+", "-", cleaned)
    return slug or "documento"


def format_status_badges(text: str) -> str:
    """Converts bracketed status tags ([PASS], [FAIL], [WARN], [INFO]) into styled HTML badges."""
    patterns = [
        (r"\[(PASS|PASSED|APROBADO|OK|EXITOSO)\]", r'<span class="badge badge-success">\1</span>'),
        (r"\[(FAIL|FAILED|FALLO|ERROR|REPROBADO)\]", r'<span class="badge badge-danger">\1</span>'),
        (r"\[(WARN|WARNING|ADVERTENCIA|PENDIENTE|PENDING)\]", r'<span class="badge badge-warning">\1</span>'),
        (r"\[(INFO|NOTA|RECOMENDADO|RECOMMENDED)\]", r'<span class="badge badge-info">\1</span>'),
    ]
    for pat, rep in patterns:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text


def inline_formatting(text: str) -> str:
    """
    Processes inline Markdown syntax (inline code, images, links, bold, italic,
    strikethrough, keyboard shortcuts, and status badges).
    """
    code_tokens: List[str] = []

    def code_repl(m: re.Match) -> str:
        code_tokens.append(f"<code>{escape(m.group(1))}</code>")
        return f"\x00INLINECODE{len(code_tokens) - 1}\x00"

    text = re.sub(r"`([^`]+)`", code_repl, text)

    text = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        r'<img src="\2" alt="\1" style="max-width: 100%; border-radius: 12px; margin: 0.6rem 0; box-shadow: var(--shadow-sm);">',
        text,
    )

    def link_repl(m: re.Match) -> str:
        link_text = m.group(1)
        href = m.group(2).strip()
        if href.startswith("#"):
            slug_href = "#" + slugify(href[1:])
            return f'<a href="{slug_href}">{link_text}</a>'
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{link_text}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.*?)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"<em>\1</em>", text)
    text = re.sub(r"~~(.*?)~~", r"<del>\1</del>", text)
    text = re.sub(r"\[\[kbd:([^\]]+)\]\]", r"<kbd>\1</kbd>", text)
    text = format_status_badges(text)

    for i, tok in enumerate(code_tokens):
        text = text.replace(f"\x00INLINECODE{i}\x00", tok)
    return text


_SYNTAX_KEYWORDS: Dict[str, str] = {
    "python": (
        r"\b(def|class|return|import|from|as|if|elif|else|for|while|try|except|"
        r"finally|raise|with|pass|lambda|yield|True|False|None|and|or|not|is|in)\b"
    ),
    "javascript": (
        r"\b(function|const|let|var|return|if|else|for|while|try|catch|finally|"
        r"throw|class|new|import|from|export|default|true|false|null|undefined|async|await)\b"
    ),
    "json": r"\b(true|false|null)\b",
    "powershell": r"\b(function|param|if|else|elseif|foreach|while|try|catch|finally|return|throw|switch)\b",
}


def highlight_code_block(code_raw: str, lang: str) -> str:
    """Applies lightweight regex-based syntax highlighting to fenced code blocks."""
    esc = escape(code_raw)
    lang_lower = (lang or "").lower().strip()
    if lang_lower == "diff":
        lines = []
        for line in esc.splitlines():
            if line.startswith("+"):
                lines.append(f'<span class="tok-diff-add">{line}</span>')
            elif line.startswith("-"):
                lines.append(f'<span class="tok-diff-del">{line}</span>')
            else:
                lines.append(line)
        return "\n".join(lines)

    kw_regex = _SYNTAX_KEYWORDS.get(lang_lower)
    if kw_regex:
        esc = re.sub(kw_regex, r'<span class="tok-kw">\1</span>', esc)
    return esc


def clean_markdown_inline(text: str) -> str:
    """Strips inline Markdown formatting and tags to extract a clean plain-text title."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[kbd:([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"\1", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    text = re.sub(
        r"\[(PASS|PASSED|APROBADO|OK|EXITOSO|FAIL|FAILED|FALLO|ERROR|REPROBADO|"
        r"WARN|WARNING|ADVERTENCIA|PENDIENTE|PENDING|INFO|NOTA|RECOMENDADO)\]",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^[#\s\-*:]+", "", text)
    return text.strip()
