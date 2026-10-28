#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Math Engine — Volcanic Amber & Deep Obsidian Design System
Módulo independiente y modular para el parseo, protección y renderizado
de fórmulas matemáticas LaTeX (Display Math $$...$$ e Inline Math $...$).
Integración autónoma 100% offline con MathJax 3 (tex-svg).
"""

import re
import html
from pathlib import Path

# Directorio de assets
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# Caché en memoria del bundle JS para inyección instantánea (< 1ms)
_mathjax_js_cache = None

# Tokens de protección para evitar interferencia del parser de Markdown (sin guiones bajos ni caracteres especiales)
_TOKEN_ESCAPED_DOLLAR = "\x00MATHESCDOLLAR\x00"
_TOKEN_BLOCK_PREFIX = "\x00MATHBLOCK"
_TOKEN_INLINE_PREFIX = "\x00MATHINLINE"

# Configuración de cliente para MathJax 3
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

# Estilos CSS de alta definición para fórmulas matemáticas
MATH_CSS_STYLES = """
/* MathJax LaTeX Rendering (100% Offline & Vectorial SVG) */
.math-block {
  margin: 1.6rem 0 2rem 0;
  padding: 1.35rem 1.6rem;
  background-color: var(--card-alt-bg);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow-x: auto;
  overflow-y: hidden;
  box-shadow: var(--shadow-sm);
  transition: border-color 200ms ease, box-shadow 200ms ease;
}

.math-block:hover {
  border-color: rgba(249, 115, 22, 0.28);
}

.math-block mjx-container[jax="SVG"] {
  margin: 0 !important;
  padding: 0.2rem 0;
  outline: none;
}

.math-block mjx-container[jax="SVG"] svg {
  max-width: 100%;
  height: auto;
  color: inherit;
}

.math-inline {
  display: inline;
  vertical-align: middle;
}

.math-inline mjx-container[jax="SVG"] {
  margin: 0 0.15rem !important;
  display: inline-block !important;
  vertical-align: -0.22em !important;
  outline: none;
}

.math-inline mjx-container[jax="SVG"] svg {
  color: inherit;
}

@media print {
  .math-block {
    box-shadow: none !important;
    border: 1px solid #cbd5e1 !important;
    background: transparent !important;
    page-break-inside: avoid;
  }
}
"""

def get_math_runtime_code() -> str:
    """
    Carga el runtime minificado de MathJax (v3 tex-svg) desde assets/ de forma 100% offline.
    Mantiene caché en memoria para velocidad de inyección ultrarrápida (< 1ms).
    """
    global _mathjax_js_cache
    if _mathjax_js_cache is not None:
        return _mathjax_js_cache

    candidates = [
        ASSETS_DIR / "tex-svg.min.js",
        Path(__file__).resolve().parent.parent / "assets" / "tex-svg.min.js",
        Path.home() / ".gemini" / "config" / "skills" / "markdown-to-html" / "references" / "tex-svg.min.js",
    ]
    for cand in candidates:
        if cand.exists():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    _mathjax_js_cache = f.read()
                return _mathjax_js_cache
            except Exception:
                pass
    return ""

def is_math_heading_or_line(line: str) -> bool:
    """
    Determina si una línea es el comienzo o delimitador de una fórmula matemática,
    evitando que sea absorbida como título del documento en detect_smart_title.
    """
    st = line.strip()
    return st.startswith(('$$', r'\[', r'\('))

class MathContext:
    """
    Contenedor de estado para el ciclo de vida del parseo y protección matemática
    en un documento. Permite tokenizar fórmulas antes de que Markdown las procese
    y restaurarlas posteriormente en contenedores HTML limpios.
    """
    def __init__(self):
        self.block_items = []
        self.inline_items = []
        self.has_math = False

    def protect_markdown(self, text: str) -> str:
        """
        Detecta y reemplaza fórmulas matemáticas en bloque y en línea con tokens opacos,
        inmunes a las transformaciones de negrita, cursiva (subíndices _) y badges.
        """
        # 1. Proteger signos de dólar escapados con barra invertida (\$12,000,000)
        text = text.replace(r"\$", _TOKEN_ESCAPED_DOLLAR)

        # 2. Extraer bloques matemáticos delimitados por $$...$$
        def block_repl_dd(m):
            raw = m.group(1).strip()
            # Restaurar el \$ dentro de la fórmula LaTeX porque MathJax lo interpreta
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.block_items)
            self.block_items.append((raw_math, "display"))
            self.has_math = True
            return f"{_TOKEN_BLOCK_PREFIX}{idx}\x00"

        text = re.sub(r"\$\$(.*?)\$\$", block_repl_dd, text, flags=re.DOTALL)

        # 3. Extraer bloques matemáticos delimitados por \[...\]
        def block_repl_bracket(m):
            raw = m.group(1).strip()
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.block_items)
            self.block_items.append((raw_math, "bracket"))
            self.has_math = True
            return f"{_TOKEN_BLOCK_PREFIX}{idx}\x00"

        text = re.sub(r"\\\[(.*?)\\\]", block_repl_bracket, text, flags=re.DOTALL)

        # 4. Extraer fórmulas en línea delimitadas por \(...\)
        def inline_repl_paren(m):
            raw = m.group(1).strip()
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.inline_items)
            self.inline_items.append((raw_math, "paren"))
            self.has_math = True
            return f"{_TOKEN_INLINE_PREFIX}{idx}\x00"

        text = re.sub(r"\\\((.*?)\\\)", inline_repl_paren, text)

        # 5. Extraer fórmulas en línea delimitadas por $...$
        # Regla estricta: No precedido por \, no seguido de espacio, no precedido de espacio antes del cierre
        def inline_repl_dollar(m):
            raw = m.group(1)
            raw_math = raw.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
            idx = len(self.inline_items)
            self.inline_items.append((raw_math, "dollar"))
            self.has_math = True
            return f"{_TOKEN_INLINE_PREFIX}{idx}\x00"

        text = re.sub(r"(?<!\\)\$(?!\s)([^\$\n]+?)(?<!\s)(?<!\\)\$", inline_repl_dollar, text)

        # 6. Restaurar \$ fuera de las fórmulas matemáticas para texto plano ordinario
        text = text.replace(_TOKEN_ESCAPED_DOLLAR, r"\$")
        return text

    def restore_html(self, text: str) -> str:
        """
        Restaura los tokens matemáticos en sus respectivos elementos HTML
        (.math-block y .math-inline) respetando el escape HTML para inyección segura.
        """
        # Restaurar fórmulas en bloque
        for idx, (formula, kind) in enumerate(self.block_items):
            token = f"{_TOKEN_BLOCK_PREFIX}{idx}\x00"
            if token in text:
                esc_formula = html.escape(formula)
                block_html = (
                    f'<div class="math-block" id="math-block-{idx + 1}">\n'
                    f'  $${esc_formula}$$\n'
                    f'</div>'
                )
                text = text.replace(token, block_html)

        # Restaurar fórmulas en línea
        for idx, (formula, kind) in enumerate(self.inline_items):
            token = f"{_TOKEN_INLINE_PREFIX}{idx}\x00"
            if token in text:
                esc_formula = html.escape(formula)
                inline_html = f'<span class="math-inline">${esc_formula}$</span>'
                text = text.replace(token, inline_html)

        return text

def build_math_block_html(formula: str, block_id: int) -> str:
    """
    Construye un bloque matemático display HTML para bloques de código ```math o ```latex.
    """
    esc_formula = html.escape(formula.strip())
    return (
        f'<div class="math-block" id="math-block-{block_id}">\n'
        f'  $${esc_formula}$$\n'
        f'</div>'
    )

def generate_math_scripts() -> str:
    """
    Genera los tags de script necesarios para MathJax 3 100% offline.
    """
    runtime_js = get_math_runtime_code()
    if not runtime_js:
        return ""
    return f"{MATHJAX_CLIENT_CONFIG}\n<script>\n{runtime_js}\n</script>"
