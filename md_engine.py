#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Compilation Engine Entrypoint & Public API Facade.
Delegates AST parsing, template loading, metadata caching, and library catalog
generation to the `md2html` Hexagonal Architecture package.
"""

from pathlib import Path

from md2html.adapters.storage.index_cache import (
    _INDEX_CACHE_LOCK,
    _TITLE_CACHE,
    get_cached_title_or_read,
    load_index_cache,
    remove_from_index_cache,
    save_index_cache,
)
from md2html.core.compiler import (
    ItemNode,
    ListNode,
    MATH_CSS_STYLES,
    MathContext,
    build_math_block_html,
    build_tree,
    clean_markdown_inline,
    compile_markdown_to_body,
    detect_smart_title,
    escape,
    find_code_block_line_indices,
    format_status_badges,
    format_stem_as_title,
    generate_math_scripts,
    get_math_runtime_code,
    highlight_code_block,
    inline_formatting,
    is_list_marker,
    is_math_heading_or_line,
    parse_list_items,
    parse_markdown,
    render_item_node,
    render_list_node,
    slugify,
    strip_fence_indent,
)
from md2html.core.services.catalog_service import (
    generate_index_html,
    generate_latest_redirect,
)
from md2html.core.services.conversion_service import convert_and_update_library
from md2html.templates.icons import (
    ALERT_ICONS,
    ICON_BOLT,
    ICON_CHEVRON_DOWN,
    ICON_CODE,
    ICON_COPY,
    ICON_DIAGRAM,
    ICON_DOC,
    ICON_EXPORT,
    ICON_EXTERNAL,
    ICON_FOLDER,
    ICON_SEARCH,
)
from md2html.templates.loader import (
    get_common_styles,
    get_html_doc_template,
    get_mermaid_client_js,
    get_mermaid_runtime_code,
)

COMMON_STYLES = get_common_styles()
HTML_DOC_TEMPLATE = get_html_doc_template()
MERMAID_CLIENT_JS = get_mermaid_client_js()

__all__ = [
    "ALERT_ICONS",
    "COMMON_STYLES",
    "HTML_DOC_TEMPLATE",
    "ICON_BOLT",
    "ICON_CHEVRON_DOWN",
    "ICON_CODE",
    "ICON_COPY",
    "ICON_DIAGRAM",
    "ICON_DOC",
    "ICON_EXPORT",
    "ICON_EXTERNAL",
    "ICON_FOLDER",
    "ICON_SEARCH",
    "ItemNode",
    "ListNode",
    "MATH_CSS_STYLES",
    "MERMAID_CLIENT_JS",
    "MathContext",
    "_INDEX_CACHE_LOCK",
    "_TITLE_CACHE",
    "build_math_block_html",
    "build_tree",
    "clean_markdown_inline",
    "compile_markdown_to_body",
    "convert_and_update_library",
    "detect_smart_title",
    "escape",
    "find_code_block_line_indices",
    "format_status_badges",
    "format_stem_as_title",
    "generate_index_html",
    "generate_latest_redirect",
    "generate_math_scripts",
    "get_cached_title_or_read",
    "get_math_runtime_code",
    "get_mermaid_runtime_code",
    "highlight_code_block",
    "inline_formatting",
    "is_list_marker",
    "is_math_heading_or_line",
    "load_index_cache",
    "parse_list_items",
    "parse_markdown",
    "remove_from_index_cache",
    "render_item_node",
    "render_list_node",
    "save_index_cache",
    "slugify",
]

if __name__ == "__main__":
    test_md = (
        "# Documento de Prueba\n\n"
        "Este es un documento de prueba para verificar el motor.\n\n"
        "- [x] Tarea 1\n"
        "- [ ] Tarea 2\n\n"
        "> [!NOTE]\n"
        "> Nota de prueba."
    )
    res = convert_and_update_library(
        test_md,
        str(Path.home() / "Downloads" / "Markdown_HTML_Library"),
        "Prueba Inicial",
    )
    print("Resultado:", res)
