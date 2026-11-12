#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown lexical/syntactic compiler subsystem."""

from md2html.core.compiler.ast_nodes import (
    ItemNode,
    ListNode,
    build_tree,
    is_list_marker,
    parse_list_items,
    render_item_node,
    render_list_node,
    strip_fence_indent,
)
from md2html.core.compiler.inline_parser import (
    clean_markdown_inline,
    escape,
    format_status_badges,
    highlight_code_block,
    inline_formatting,
    slugify,
)
from md2html.core.compiler.markdown_parser import (
    compile_markdown_to_body,
    parse_markdown,
)
from md2html.core.compiler.math_protector import (
    MATH_CSS_STYLES,
    MATHJAX_CLIENT_CONFIG,
    MathContext,
    _TOKEN_BLOCK_PREFIX,
    _TOKEN_ESCAPED_DOLLAR,
    _TOKEN_INLINE_PREFIX,
    build_math_block_html,
    generate_math_scripts,
    get_math_runtime_code,
    is_math_heading_or_line,
)
from md2html.core.compiler.title_detector import (
    detect_smart_title,
    find_code_block_line_indices,
    format_stem_as_title,
)

__all__ = [
    "ItemNode",
    "ListNode",
    "MATHJAX_CLIENT_CONFIG",
    "MATH_CSS_STYLES",
    "MathContext",
    "_TOKEN_BLOCK_PREFIX",
    "_TOKEN_ESCAPED_DOLLAR",
    "_TOKEN_INLINE_PREFIX",
    "build_math_block_html",
    "build_tree",
    "clean_markdown_inline",
    "compile_markdown_to_body",
    "detect_smart_title",
    "escape",
    "find_code_block_line_indices",
    "format_status_badges",
    "format_stem_as_title",
    "generate_math_scripts",
    "get_math_runtime_code",
    "highlight_code_block",
    "inline_formatting",
    "is_list_marker",
    "is_math_heading_or_line",
    "parse_list_items",
    "parse_markdown",
    "render_item_node",
    "render_list_node",
    "slugify",
    "strip_fence_indent",
]
