#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX mathematical expression tokenizer and offline MathJax 3 SVG injector.
Protects display ($$...$$, \\[...\\]) and inline ($...$, \\(...\\)) math formulas
with opaque tokens prior to Markdown inline/block parsing.
"""

import html
import re
from typing import List, Tuple

from md2html.templates.loader import get_math_runtime_code, get_math_styles

_TOKEN_ESCAPED_DOLLAR = "\x00MATHESCDOLLAR\x00"
_TOKEN_BLOCK_PREFIX = "\x00MATHBLOCK"
_TOKEN_INLINE_PREFIX = "\x00MATHINLINE"

MATHJAX_CLIENT_CONFIG = """
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true,
    processEnvironments: true
  },
  svg: {
    fontCache: 'local'
  },
  options: {
    enableMenu: false
  }
};
</script>
"""

MATH_CSS_STYLES = get_math_styles()


def is_math_heading_or_line(line: str) -> bool:
    """Checks whether a line starts with a display or inline math delimiter."""
    st = line.strip()
    return st.startswith(("$$", r"\[", r"\("))


class MathContext:
    """
    Stateful tokenizer for a single Markdown compilation pass.
    Replaces LaTeX formulas with opaque null-delimited tokens before Markdown
    processing and restores them as sanitized HTML containers afterward.
    """

    def __init__(self) -> None:
        self.block_items: List[Tuple[str, str]] = []
        self.inline_items: List[Tuple[str, str]] = []
        self.has_math: bool = False

    def protect_markdown(self, text: str) -> str:
        """Replaces block and inline math expressions with opaque tokens."""
        text = text.replace(r"\$", _TOKEN_ESCAPED_DOLLAR)

        def block_repl_dd(m: re.Match) -> str:
            raw = m.group(1).strip()
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.block_items)
            self.block_items.append((raw_math, "display"))
            self.has_math = True
            return f"{_TOKEN_BLOCK_PREFIX}{idx}\x00"

        text = re.sub(r"\$\$(.*?)\$\$", block_repl_dd, text, flags=re.DOTALL)

        def block_repl_bracket(m: re.Match) -> str:
            raw = m.group(1).strip()
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.block_items)
            self.block_items.append((raw_math, "bracket"))
            self.has_math = True
            return f"{_TOKEN_BLOCK_PREFIX}{idx}\x00"

        text = re.sub(r"\\\[(.*?)\\\]", block_repl_bracket, text, flags=re.DOTALL)

        def inline_repl_paren(m: re.Match) -> str:
            raw = m.group(1).strip()
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.inline_items)
            self.inline_items.append((raw_math, "paren"))
            self.has_math = True
            return f"{_TOKEN_INLINE_PREFIX}{idx}\x00"

        text = re.sub(r"\\\((.*?)\\\)", inline_repl_paren, text)

        def inline_repl_dollar(m: re.Match) -> str:
            raw = m.group(1)
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.inline_items)
            self.inline_items.append((raw_math, "dollar"))
            self.has_math = True
            return f"{_TOKEN_INLINE_PREFIX}{idx}\x00"

        text = re.sub(
            r"(?<!\\)\$(?!\s)([^\$\n]+?)(?<!\s)(?<!\\)\$",
            inline_repl_dollar,
            text,
        )

        text = text.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
        return text

    def restore_html(self, text: str) -> str:
        """Restores math tokens into HTML .math-block and .math-inline elements."""
        for idx, (formula, _kind) in enumerate(self.block_items):
            token = f"{_TOKEN_BLOCK_PREFIX}{idx}\x00"
            if token in text:
                esc_formula = html.escape(formula)
                block_html = (
                    f'<div class="math-block" id="math-block-{idx + 1}">\n'
                    f"  $${esc_formula}$$\n"
                    f"</div>"
                )
                text = text.replace(token, block_html)

        for idx, (formula, _kind) in enumerate(self.inline_items):
            token = f"{_TOKEN_INLINE_PREFIX}{idx}\x00"
            if token in text:
                esc_formula = html.escape(formula)
                inline_html = f'<span class="math-inline">${esc_formula}$</span>'
                text = text.replace(token, inline_html)

        return text


def build_math_block_html(formula: str, block_id: int) -> str:
    """Builds a display math HTML container for fenced ```math or ```equation blocks."""
    esc_formula = html.escape(formula.strip())
    return (
        f'<div class="math-block" id="math-block-{block_id}">\n'
        f"  $${esc_formula}$$\n"
        f"</div>"
    )


def generate_math_scripts() -> str:
    """Generates the inline script tags for offline MathJax 3 SVG rendering."""
    runtime_js = get_math_runtime_code()
    if not runtime_js:
        return ""
    return f"{MATHJAX_CLIENT_CONFIG}\n<script>\n{runtime_js}\n</script>"
