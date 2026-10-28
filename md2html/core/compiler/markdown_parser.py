#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-pass Markdown lexical and syntactic compiler.
Transforms Markdown documents into structured HTML with TOC, GitHub callout alerts,
interactive Mermaid diagram cards, LaTeX MathJax blocks, and responsive tables.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from md2html.core.compiler.ast_nodes import (
    build_tree,
    is_list_marker,
    parse_list_items,
    render_list_node,
)
from md2html.core.compiler.inline_parser import (
    escape,
    highlight_code_block,
    inline_formatting,
    slugify,
)
from md2html.core.compiler.math_protector import (
    _TOKEN_BLOCK_PREFIX,
    MathContext,
    build_math_block_html,
)
from md2html.core.compiler.title_detector import detect_smart_title
from md2html.templates.icons import ALERT_ICONS, ICON_CODE, ICON_COPY, ICON_DIAGRAM


def _build_mermaid_card_html(diag_id: str, esc_code: str) -> str:
    """Builds the interactive HTML container for a Mermaid diagram block."""
    return (
        f'<div class="mermaid-block" id="block-{diag_id}">\n'
        f'  <div class="mermaid-header">\n'
        f'    <div class="mermaid-title">\n'
        f"      {ICON_DIAGRAM}\n"
        f"      <span>Diagrama Mermaid</span>\n"
        f"    </div>\n"
        f'    <div class="mermaid-actions">\n'
        f'      <button class="copy-btn toggle-source-btn" onclick="toggleMermaidSource(\'{diag_id}\', this)" title="Ver u ocultar código Mermaid">\n'
        f"        {ICON_CODE}\n"
        f"        <span>Ver código</span>\n"
        f"      </button>\n"
        f'      <button class="copy-btn" onclick="copyMermaidSource(\'{diag_id}\', this)" title="Copiar definición Mermaid">\n'
        f"        {ICON_COPY}\n"
        f"        <span>Copiar</span>\n"
        f"      </button>\n"
        f"    </div>\n"
        f"  </div>\n"
        f'  <div class="mermaid-render" id="render-{diag_id}">\n'
        f'    <div class="mermaid-loading">Cargando diagrama...</div>\n'
        f"  </div>\n"
        f'  <div class="mermaid-source" id="source-{diag_id}" style="display: none;">\n'
        f'    <pre><code class="language-mermaid">{esc_code}</code></pre>\n'
        f"  </div>\n"
        f'  <div id="raw-{diag_id}" style="display: none;">{esc_code}</div>\n'
        f"</div>"
    )


def _render_table_block(table_lines: List[str], has_separator: bool) -> str:
    """Renders a contiguous sequence of Markdown table lines into a .table-container HTML block."""
    if has_separator:
        headers = [c.strip() for c in table_lines[0].strip().strip("|").split("|")]
        align_cells = [c.strip() for c in table_lines[1].strip().strip("|").split("|")]
        alignments = []
        for a in align_cells:
            if a.startswith(":") and a.endswith(":"):
                alignments.append('style="text-align: center;"')
            elif a.endswith(":"):
                alignments.append('style="text-align: right;"')
            elif a.startswith(":"):
                alignments.append('style="text-align: left;"')
            else:
                alignments.append("")
        data_rows = table_lines[2:]
    else:
        headers = [c.strip() for c in table_lines[0].strip().strip("|").split("|")]
        alignments = ["" for _ in headers]
        data_rows = table_lines[1:]

    th_html = "".join(
        [
            f"<th {alignments[col] if col < len(alignments) else ''}>{inline_formatting(h)}</th>"
            for col, h in enumerate(headers)
        ]
    )
    tr_html = []
    for r_line in data_rows:
        cells = [c.strip() for c in r_line.strip().strip("|").split("|")]
        tds = "".join(
            [
                f"<td {alignments[col] if col < len(alignments) else ''}>{inline_formatting(c)}</td>"
                for col, c in enumerate(cells)
            ]
        )
        tr_html.append(f"<tr>{tds}</tr>")

    return (
        f'<div class="table-container">\n'
        f"  <table>\n"
        f"    <thead><tr>{th_html}</tr></thead>\n"
        f'    <tbody>{"".join(tr_html)}</tbody>\n'
        f"  </table>\n"
        f"</div>"
    )


def parse_markdown(
    md_text: str,
    custom_title: Optional[str] = None,
    input_file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compiles raw Markdown text into a structured dictionary containing the HTML body,
    detected title, table of contents, YAML frontmatter, and runtime feature flags.
    """
    md_text = md_text.lstrip("\ufeff")

    math_ctx = MathContext()
    md_text = math_ctx.protect_markdown(md_text)

    lines = md_text.splitlines()

    frontmatter: Dict[str, str] = {}
    idx = 0
    if len(lines) > 0 and lines[0].strip() == "---":
        idx = 1
        fm_lines = []
        while idx < len(lines) and lines[idx].strip() != "---":
            fm_lines.append(lines[idx])
            idx += 1
        if idx < len(lines):
            idx += 1
            for fml in fm_lines:
                if ":" in fml:
                    k, v = fml.split(":", 1)
                    frontmatter[k.strip().lower()] = v.strip().strip('"').strip("'")

    body_lines = lines[idx:]

    smart_title, title_src, title_line_idx = detect_smart_title(
        lines=body_lines,
        custom_title=custom_title,
        input_file_path=input_file_path,
        frontmatter=frontmatter,
    )

    html_blocks: List[str] = []
    toc_items: List[Tuple[int, str, str]] = []
    title_line_consumed = False
    mermaid_count = 0
    has_mermaid = False

    i = 0
    n = len(body_lines)
    while i < n:
        loop_start_i = i
        line = body_lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if not title_line_consumed and i == title_line_idx:
            title_line_consumed = True
            i += 2 if title_src in ("setext_h1", "setext_h2") else 1
            continue

        if stripped.startswith(_TOKEN_BLOCK_PREFIX) and stripped.endswith("\x00"):
            html_blocks.append(stripped)
            i += 1
            continue

        # Setext headings not consumed as document title
        if i + 1 < n and stripped and not stripped.startswith(("#", "```", ">", "|", "- ", "* ", "+ ", "---", "===")):
            next_line = body_lines[i + 1].strip()
            if re.match(r"^[=]{3,}\s*$", next_line):
                slug = slugify(stripped)
                heading_content = inline_formatting(stripped)
                html_blocks.append(f'<h1 id="{slug}">{heading_content}</h1>')
                i += 2
                continue
            elif re.match(r"^[-]{3,}\s*$", next_line) and not stripped.startswith("-"):
                slug = slugify(stripped)
                toc_items.append((2, stripped, slug))
                heading_content = inline_formatting(stripped)
                html_blocks.append(f'<h2 id="{slug}">{heading_content}</h2>')
                i += 2
                continue

        # Fenced code blocks (standard, Mermaid, and LaTeX math)
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < n and not body_lines[i].strip().startswith("```"):
                code_lines.append(body_lines[i])
                i += 1
            if i < n:
                i += 1
            code_raw = "\n".join(code_lines)
            lang_lower = (lang or "").lower().strip()

            if lang_lower == "mermaid":
                mermaid_count += 1
                has_mermaid = True
                diag_id = f"mermaid-{mermaid_count}"
                html_blocks.append(_build_mermaid_card_html(diag_id, escape(code_raw)))
                continue

            if lang_lower in ("math", "equation"):
                math_block_id = len(math_ctx.block_items) + 1
                math_ctx.has_math = True
                html_blocks.append(build_math_block_html(code_raw, math_block_id))
                continue

            code_html = highlight_code_block(code_raw, lang)
            lang_label = escape(lang.upper() if lang else "CODE")
            html_blocks.append(
                f'<div class="code-block">\n'
                f'  <div class="code-header">\n'
                f"    <span>{lang_label}</span>\n"
                f'    <button class="copy-btn" onclick="copyCode(this)">{ICON_COPY}<span>Copiar</span></button>\n'
                f"  </div>\n"
                f"  <pre><code>{code_html}</code></pre>\n"
                f"</div>"
            )
            continue

        # ATX Headings (# to ######)
        heading_match = re.match(r"^\s*(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_raw = heading_match.group(2).strip()
            slug = slugify(heading_raw)

            if level in (2, 3):
                toc_items.append((level, heading_raw, slug))

            heading_content = inline_formatting(heading_raw)
            html_blocks.append(f'<h{level} id="{slug}">{heading_content}</h{level}>')
            i += 1
            continue

        # Callout Alerts (> [!NOTE], > [!TIP], etc.)
        alert_match = re.match(
            r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$",
            line,
            re.IGNORECASE,
        )
        if alert_match:
            alert_type = alert_match.group(1).lower()
            alert_header_text = alert_match.group(2).strip() or alert_type.upper()
            alert_body_lines = []
            i += 1
            while i < n and (body_lines[i].strip().startswith(">") or not body_lines[i].strip()):
                if body_lines[i].strip().startswith(">"):
                    sub_line = re.sub(r"^\s*>\s?", "", body_lines[i])
                    alert_body_lines.append(sub_line)
                i += 1
            alert_icon = ALERT_ICONS.get(alert_type, ALERT_ICONS["note"])
            alert_body_html = "<br>".join([inline_formatting(l) for l in alert_body_lines if l.strip()])
            html_blocks.append(
                f'<div class="alert alert-{alert_type}">\n'
                f'  <div class="alert-header">{alert_icon} <span>{alert_header_text}</span></div>\n'
                f"  <div>{alert_body_html}</div>\n"
                f"</div>"
            )
            continue

        # Standard Blockquote
        if stripped.startswith(">"):
            bq_lines = []
            while i < n and (body_lines[i].strip().startswith(">") or not body_lines[i].strip()):
                if body_lines[i].strip().startswith(">"):
                    bq_lines.append(re.sub(r"^\s*>\s?", "", body_lines[i]))
                i += 1
            bq_content = "<br>".join([inline_formatting(l) for l in bq_lines if l.strip()])
            html_blocks.append(f"<blockquote><p>{bq_content}</p></blockquote>")
            continue

        # Tables (with alignment row or continuous pipe rows)
        has_table_syntax = (
            ("|" in stripped and i + 1 < n and re.match(r"^\s*\|?\s*:?---", body_lines[i + 1]))
            or (
                stripped.startswith("|")
                and stripped.endswith("|")
                and i + 1 < n
                and body_lines[i + 1].strip().startswith("|")
                and body_lines[i + 1].strip().endswith("|")
            )
        )
        if has_table_syntax:
            table_lines = [line]
            peek = i + 1
            has_separator = re.match(r"^\s*\|?\s*:?---", body_lines[peek]) is not None
            while peek < n:
                nxt_str = body_lines[peek].strip()
                if has_separator:
                    if "|" in nxt_str:
                        table_lines.append(body_lines[peek])
                        peek += 1
                    else:
                        break
                else:
                    if nxt_str.startswith("|") and nxt_str.endswith("|"):
                        table_lines.append(body_lines[peek])
                        peek += 1
                    else:
                        break

            if len(table_lines) >= 2:
                html_blocks.append(_render_table_block(table_lines, has_separator))
                i = peek
                continue

        # Horizontal Rule
        if re.match(r"^(?:[-*_]\s*){3,}$", stripped):
            html_blocks.append("<hr>")
            i += 1
            continue

        # Lists
        if is_list_marker(line):
            raw_items, next_i = parse_list_items(body_lines, i)
            if next_i <= i:
                next_i = i + 1
            roots = build_tree(raw_items)
            for r in roots:
                html_blocks.append(render_list_node(r))
            i = next_i
            continue

        # Paragraphs
        para_lines = []
        while (
            i < n
            and body_lines[i].strip()
            and not re.match(r"^\s*#{1,6}\s+", body_lines[i])
            and not body_lines[i].strip().startswith("```")
            and not body_lines[i].strip().startswith(">")
            and not body_lines[i].strip().startswith(_TOKEN_BLOCK_PREFIX)
            and not (
                ("|" in body_lines[i] and i + 1 < n and re.match(r"^\s*\|?\s*:?---", body_lines[i + 1]))
                or (
                    body_lines[i].strip().startswith("|")
                    and body_lines[i].strip().endswith("|")
                    and i + 1 < n
                    and body_lines[i + 1].strip().startswith("|")
                    and body_lines[i + 1].strip().endswith("|")
                )
            )
            and not re.match(r"^(?:[-*_]\s*){3,}$", body_lines[i].strip())
            and not is_list_marker(body_lines[i])
            and not (i + 1 < n and re.match(r"^[=\-]{3,}\s*$", body_lines[i + 1].strip()))
        ):
            para_lines.append(body_lines[i].strip())
            i += 1
        if para_lines:
            para_text = " ".join(para_lines)
            html_blocks.append(f"<p>{inline_formatting(para_text)}</p>")

        if i == loop_start_i:
            html_blocks.append(f"<p>{inline_formatting(stripped)}</p>")
            i += 1

    toc_html = ""
    if len(toc_items) >= 3:
        toc_li = []
        for lvl, text, slug in toc_items:
            pad = "&nbsp;&nbsp;" if lvl == 3 else ""
            toc_li.append(f'<li>{pad}<a href="#{slug}">{escape(text)}</a></li>')
        toc_html = (
            f'<details class="toc-box" open>\n'
            f"  <summary>📑 Índice de Contenidos</summary>\n"
            f'  <nav class="toc-nav"><ul>{"".join(toc_li)}</ul></nav>\n'
            f"</details>"
        )

    raw_body = "\n".join(html_blocks)
    final_body = math_ctx.restore_html(raw_body)
    final_title = smart_title or "Documento"

    return {
        "title": final_title,
        "badge": "",
        "subtitle": "",
        "body": final_body,
        "toc": toc_html,
        "frontmatter": frontmatter,
        "has_mermaid": has_mermaid,
        "has_math": math_ctx.has_math,
    }


def compile_markdown_to_body(
    md_text: str,
    custom_title: Optional[str] = None,
    input_file_path: Optional[str] = None,
) -> str:
    """Compiles Markdown text directly into an HTML body fragment."""
    return parse_markdown(md_text, custom_title=custom_title, input_file_path=input_file_path)["body"]
