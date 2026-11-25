#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inline Markdown formatting, slug generation, status badges, and syntax highlighting.
"""

import html
import re
import unicodedata
from typing import List, Tuple

from md2html.core.compiler.syntax_highlighter import highlight_code


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


_LINK_TARGET_RE = r"((?:\([^()\n]*\)|[^()\n])+)"


def _split_markdown_link_tags(raw_target: str) -> Tuple[str, str]:
    r"""
    Resolves opening and closing <a> HTML tags for a Markdown link target:
    - Internet URLs (http, https, mailto): active link with target="_blank" and rel="noopener noreferrer".
    - Anchors and local library navigation (#, ./index.html, ./latest.html): active local link.
    - Local file paths (file://, C:\, .pdf, .md, .docx, etc.): deactivated (empty tag pair).
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
        return f'<a href="{esc_href}"{title_attr} target="_blank" rel="noopener noreferrer">', "</a>"

    # Case 2: Internal anchor within document
    if href.startswith("#"):
        slug_href = "#" + slugify(href[1:])
        return f'<a href="{slug_href}"{title_attr}>', "</a>"

    # Case 3: Local catalog navigation (index.html, latest.html)
    if any(href_lower.startswith(prefix) for prefix in _LOCAL_NAV_PREFIXES):
        esc_href = escape(href)
        return f'<a href="{esc_href}"{title_attr}>', "</a>"

    # Case 4: File links and local paths ("los de archivos y así no")
    if _is_local_file_target(href):
        return "", ""

    # Default fallback: If it looks like a web domain without protocol (e.g. www.example.com)
    if href_lower.startswith("www."):
        esc_href = escape("https://" + href)
        return f'<a href="{esc_href}"{title_attr} target="_blank" rel="noopener noreferrer">', "</a>"

    # Otherwise, avoid creating broken links for unrecognized local paths
    return "", ""


def _format_markdown_link(link_text: str, raw_target: str) -> str:
    r"""
    Formats a Markdown link according to destination:
    - Internet URLs (http, https, mailto): active link with target="_blank" and rel="noopener noreferrer".
    - Anchors and local library navigation (#, ./index.html, ./latest.html): active local link.
    - Local file paths (file://, C:\, .pdf, .md, .docx, etc.): deactivated / safe plain text.
    """
    open_tag, close_tag = _split_markdown_link_tags(raw_target)
    if not open_tag:
        return link_text
    return f"{open_tag}{link_text}{close_tag}"


def _extract_code_span_content(ticks: str, content: str) -> str:
    """Normalizes multi-backtick inline code content per CommonMark spacing rules."""
    if len(ticks) > 1 and len(content) >= 2 and content.startswith(" ") and content.endswith(" ") and content.strip():
        return content[1:-1]
    return content


def inline_formatting(text: str) -> str:
    """
    Processes inline Markdown syntax (inline code, images, links, bold, italic,
    strikethrough, keyboard shortcuts, and status badges).
    """
    code_tokens: List[str] = []
    tag_tokens: List[str] = []

    def stash_tag(tag_html: str) -> str:
        tag_tokens.append(tag_html)
        return f"\x00INLINETAG{len(tag_tokens) - 1}\x00"

    def code_repl(m: re.Match) -> str:
        content = _extract_code_span_content(m.group(1), m.group(2))
        code_tokens.append(f"<code>{escape(content)}</code>")
        return f"\x00INLINECODE{len(code_tokens) - 1}\x00"

    text = re.sub(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", code_repl, text)

    def img_repl(m: re.Match) -> str:
        alt_esc = escape(m.group(1)).replace('"', "&quot;")
        src_esc = escape(m.group(2).strip()).replace('"', "&quot;")
        return stash_tag(
            f'<img src="{src_esc}" alt="{alt_esc}" '
            'style="max-width: 100%; border-radius: 12px; margin: 0.6rem 0; box-shadow: var(--shadow-sm);">'
        )

    text = re.sub(rf"!\[([^\]]*)\]\({_LINK_TARGET_RE}\)", img_repl, text)

    def autolink_repl(m: re.Match) -> str:
        url = m.group(1).strip()
        esc_url = escape(url)
        return stash_tag(f'<a href="{esc_url}" target="_blank" rel="noopener noreferrer">{esc_url}</a>')

    text = re.sub(r"<(https?://[^>\s]+)>", autolink_repl, text)
    text = re.sub(r"<(mailto:[^>\s]+)>", autolink_repl, text)

    def email_autolink_repl(m: re.Match) -> str:
        email = m.group(1).strip()
        esc_email = escape(email)
        return stash_tag(f'<a href="mailto:{esc_email}" target="_blank" rel="noopener noreferrer">{esc_email}</a>')

    text = re.sub(r"<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>", email_autolink_repl, text)

    def kbd_repl(m: re.Match) -> str:
        return stash_tag(f"<kbd>{escape(m.group(1))}</kbd>")

    text = re.sub(r"\[\[kbd:([^\]]+)\]\]", kbd_repl, text)

    def link_repl(m: re.Match) -> str:
        link_text = m.group(1)
        raw_target = m.group(2)
        open_tag, close_tag = _split_markdown_link_tags(raw_target)
        if not open_tag:
            return link_text
        return f"{stash_tag(open_tag)}{link_text}{stash_tag(close_tag)}"

    text = re.sub(rf"\[([^\]]+)\]\({_LINK_TARGET_RE}\)", link_repl, text)
    text = re.sub(r"(?<!\\)\\\|", "|", text)
    text = re.sub(r"\*\*\*(?!\s)(.+?)(?<!\s)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"(?<!\\)(?<!\w)__(?!_)(?!\s)(.+?)(?<!\s)(?<!\\)(?<!_)__(?!\w)",
        r"<strong>\1</strong>",
        text,
    )
    text = re.sub(r"(?<!\*)\*(?!\*)(?!\s)(.+?)(?<!\s)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"(?<!\\)(?<!\w)_(?!_)(?!\s)(.+?)(?<!\s)(?<!\\)(?<!_)_(?!\w)",
        r"<em>\1</em>",
        text,
    )
    text = re.sub(r"~~(.*?)~~", r"<del>\1</del>", text)
    text = format_status_badges(text)

    for i, tok in enumerate(tag_tokens):
        text = text.replace(f"\x00INLINETAG{i}\x00", tok)
    for i, tok in enumerate(code_tokens):
        text = text.replace(f"\x00INLINECODE{i}\x00", tok)
    return text


def highlight_code_block(code_raw: str, lang: str) -> str:
    """Applies zero-bloatware lexical syntax highlighting to fenced code blocks."""
    return highlight_code(code_raw, lang)


def clean_markdown_inline(text: str) -> str:
    """Strips inline Markdown formatting and tags to extract a clean plain-text title."""
    if not text:
        return ""
    code_tokens: List[str] = []

    def _stash_code(m: re.Match) -> str:
        code_tokens.append(_extract_code_span_content(m.group(1), m.group(2)))
        return f"\x00CLEANCODE{len(code_tokens) - 1}\x00"

    text = re.sub(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", _stash_code, text)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = re.sub(r"<(mailto:[^>]+)>", r"\1", text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    text = re.sub(rf"!\[([^\]]*)\]\({_LINK_TARGET_RE}\)", r"\1", text)
    text = re.sub(rf"\[([^\]]+)\]\({_LINK_TARGET_RE}\)", r"\1", text)
    text = re.sub(r"\[\[kbd:([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"(?<!\\)\\\|", "|", text)
    text = re.sub(r"\*\*\*(?!\s)(.+?)(?<!\s)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", r"\1", text)
    text = re.sub(
        r"(?<!\\)(?<!\w)__(?!_)(?!\s)(.+?)(?<!\s)(?<!\\)(?<!_)__(?!\w)",
        r"\1",
        text,
    )
    text = re.sub(r"(?<!\*)\*(?!\*)(?!\s)(.+?)(?<!\s)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(
        r"(?<!\\)(?<!\w)_(?!_)(?!\s)(.+?)(?<!\s)(?<!\\)(?<!_)_(?!\w)",
        r"\1",
        text,
    )
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    text = re.sub(
        r"\[(PASS|PASSED|APROBADO|OK|EXITOSO|FAIL|FAILED|FALLO|ERROR|REPROBADO|"
        r"WARN|WARNING|ADVERTENCIA|PENDIENTE|PENDING|INFO|NOTA|RECOMENDADO)\]",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^[#\s\-*:]+", "", text)
    for i, tok in enumerate(code_tokens):
        text = text.replace(f"\x00CLEANCODE{i}\x00", tok)
    return text.strip()
