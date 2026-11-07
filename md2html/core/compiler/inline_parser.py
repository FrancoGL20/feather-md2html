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


_WEB_SCHEMES = ("https://", "http://", "mailto:")
_LOCAL_NAV_PREFIXES = ("#", "./index.html", "./latest.html", "index.html", "latest.html")
_LOCAL_FILE_EXTENSIONS = (
    r"\.(pdf|docx?|xlsx?|pptx?|md|txt|rtf|csv|tsv|zip|rar|7z|tar|gz|"
    r"exe|msi|bat|cmd|ps1|sh|py|java|cpp|c|h|cs|js|ts|json|xml|yaml|yml|"
    r"png|jpg|jpeg|gif|webp|svg|ico)$"
)


def _is_local_file_target(href: str) -> bool:
    """Detects whether a URL or path points to a local file or local filesystem path."""
    h = href.strip().lower()
    if h.startswith(("file://", "file:/")):
        return True
    if re.match(r"^[a-zA-Z]:[\\/]", h) or h.startswith(("\\\\", "//")):
        return True
    if re.search(_LOCAL_FILE_EXTENSIONS, h, re.IGNORECASE):
        return True
    return False


def _format_markdown_link(link_text: str, raw_target: str) -> str:
    r"""
    Formats a Markdown link according to destination:
    - Internet URLs (http, https, mailto): active link with target="_blank" and rel="noopener noreferrer".
    - Anchors and local library navigation (#, ./index.html, ./latest.html): active local link.
    - Local file paths (file://, C:\, .pdf, .md, .docx, etc.): deactivated / safe plain text.
    """
    raw_target = raw_target.strip()
    title_match = re.match(r'^(\S+)(?:\s+["\'](.*?)["\'])?$', raw_target)
    if title_match:
        href = title_match.group(1).strip()
        link_title = title_match.group(2) or ""
    else:
        href = raw_target
        link_title = ""

    title_attr = f' title="{escape(link_title)}"' if link_title else ""
    href_lower = href.lower()

    # Case 1: Internet URLs (web protocols)
    if any(href_lower.startswith(scheme) for scheme in _WEB_SCHEMES):
        esc_href = escape(href)
        return f'<a href="{esc_href}"{title_attr} target="_blank" rel="noopener noreferrer">{link_text}</a>'

    # Case 2: Internal anchor within document
    if href.startswith("#"):
        slug_href = "#" + slugify(href[1:])
        return f'<a href="{slug_href}"{title_attr}>{link_text}</a>'

    # Case 3: Local catalog navigation (index.html, latest.html)
    if any(href_lower.startswith(prefix) for prefix in _LOCAL_NAV_PREFIXES):
        esc_href = escape(href)
        return f'<a href="{esc_href}"{title_attr}>{link_text}</a>'

    # Case 4: File links and local paths ("los de archivos y así no")
    if _is_local_file_target(href):
        return link_text

    # Default fallback: If it looks like a web domain without protocol (e.g. www.example.com)
    if href_lower.startswith("www."):
        esc_href = escape("https://" + href)
        return f'<a href="{esc_href}"{title_attr} target="_blank" rel="noopener noreferrer">{link_text}</a>'

    # Otherwise, avoid creating broken links for unrecognized local paths
    return link_text


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

    def autolink_repl(m: re.Match) -> str:
        url = m.group(1).strip()
        esc_url = escape(url)
        return f'<a href="{esc_url}" target="_blank" rel="noopener noreferrer">{esc_url}</a>'

    text = re.sub(r"<(https?://[^>\s]+)>", autolink_repl, text)
    text = re.sub(r"<(mailto:[^>\s]+)>", autolink_repl, text)

    def email_autolink_repl(m: re.Match) -> str:
        email = m.group(1).strip()
        esc_email = escape(email)
        return f'<a href="mailto:{esc_email}" target="_blank" rel="noopener noreferrer">{esc_email}</a>'

    text = re.sub(r"<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>", email_autolink_repl, text)

    def link_repl(m: re.Match) -> str:
        link_text = m.group(1)
        raw_target = m.group(2)
        return _format_markdown_link(link_text, raw_target)

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
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = re.sub(r"<(mailto:[^>]+)>", r"\1", text)
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
