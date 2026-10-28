#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown-to-HTML conversion use-case service.
Compiles Markdown input, injects offline runtimes (Mermaid/MathJax) only when
needed, writes the standalone HTML document, and updates library indices.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from md2html.core.compiler.inline_parser import escape, slugify
from md2html.core.compiler.markdown_parser import parse_markdown
from md2html.core.compiler.math_protector import generate_math_scripts
from md2html.core.services.catalog_service import (
    generate_index_html,
    generate_latest_redirect,
)
from md2html.templates.icons import ICON_BOLT, ICON_FOLDER
from md2html.templates.loader import (
    get_common_styles,
    get_html_doc_template,
    get_mermaid_client_js,
    get_mermaid_runtime_code,
)

_GENERIC_STEMS = frozenset(
    {"temp", "input", "a", "b", "test", "tmp", "untitled", "document", "documento"}
)


def convert_and_update_library(
    md_text: str,
    root_dir_str: str,
    custom_title: Optional[str] = None,
    input_file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compiles Markdown to a standalone HTML document, persists it to root_dir_str,
    regenerates index.html and latest.html, and returns conversion metadata.
    """
    try:
        root_dir = Path(root_dir_str).resolve()
        root_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        root_dir = (Path.home() / "Downloads" / "Markdown_HTML_Library").resolve()
        root_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_markdown(
        md_text,
        custom_title=custom_title,
        input_file_path=input_file_path,
    )
    final_title = parsed["title"]

    words = len(re.findall(r"\w+", md_text))
    minutes = max(1, round(words / 190))
    reading_time = f"~{minutes} min de lectura"
    now = datetime.now()
    now_str = now.strftime("%d/%m/%Y %I:%M %p")

    if (
        input_file_path
        and Path(input_file_path).exists()
        and Path(input_file_path).stem.lower() not in _GENERIC_STEMS
    ):
        base_slug = slugify(Path(input_file_path).stem)
    else:
        base_slug = slugify(final_title)

    filename = f"{base_slug}.html"
    out_path = root_dir / filename

    if out_path.exists():
        time_suffix = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{base_slug}_{time_suffix}.html"
        out_path = root_dir / filename

    mermaid_injection = ""
    if parsed.get("has_mermaid"):
        runtime_js = get_mermaid_runtime_code()
        client_js = get_mermaid_client_js()
        if runtime_js:
            mermaid_injection = f"  <script>\n{runtime_js}\n  </script>\n  <script>\n{client_js}\n  </script>"
        else:
            mermaid_injection = f"  <script>\n{client_js}\n  </script>"

    math_injection = ""
    if parsed.get("has_math"):
        math_injection = generate_math_scripts()

    template = get_html_doc_template()
    html_out = template.format(
        title=escape(final_title),
        styles=get_common_styles(),
        header_title=escape(final_title),
        header_badge="",
        header_subtitle="",
        body_content=parsed["body"],
        toc_content=parsed["toc"],
        reading_time=reading_time,
        word_count=f"{words:,}",
        generated_date=now_str,
        footer_date=now_str,
        icon_folder=ICON_FOLDER,
        icon_bolt=ICON_BOLT,
        mermaid_scripts=mermaid_injection,
        math_scripts=math_injection,
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    index_file = generate_index_html(root_dir, known_titles={filename: final_title})
    latest_file = generate_latest_redirect(root_dir, out_path, final_title)

    return {
        "success": True,
        "file_path": str(out_path),
        "file_url": f"file:///{out_path.as_posix()}",
        "filename": out_path.name,
        "title": final_title,
        "index_path": str(index_file),
        "index_url": f"file:///{index_file.as_posix()}",
        "latest_url": f"file:///{latest_file.as_posix()}",
        "words": words,
        "reading_time": reading_time,
        "root_dir": str(root_dir),
        "timestamp": now_str,
    }
