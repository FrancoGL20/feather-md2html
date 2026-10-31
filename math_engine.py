#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math Engine Public Facade.
Re-exports the LaTeX mathematical tokenizer and offline MathJax 3 SVG injector
from `md2html.core.compiler.math_protector`.
"""

from md2html.core.compiler.math_protector import (
    MATHJAX_CLIENT_CONFIG,
    MATH_CSS_STYLES,
    MathContext,
    _TOKEN_BLOCK_PREFIX,
    _TOKEN_ESCAPED_DOLLAR,
    _TOKEN_INLINE_PREFIX,
    build_math_block_html,
    generate_math_scripts,
    get_math_runtime_code,
    is_math_heading_or_line,
)

__all__ = [
    "MATHJAX_CLIENT_CONFIG",
    "MATH_CSS_STYLES",
    "MathContext",
    "_TOKEN_BLOCK_PREFIX",
    "_TOKEN_ESCAPED_DOLLAR",
    "_TOKEN_INLINE_PREFIX",
    "build_math_block_html",
    "generate_math_scripts",
    "get_math_runtime_code",
    "is_math_heading_or_line",
]
