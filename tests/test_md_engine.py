#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and Integration tests for Markdown Compilation Engine (md_engine.py).
Tests all lexical parsing, AST compilation, alerts, tables, lists, smart titles,
and catalog generation.
"""

import os
import sys
import time
import unittest
from pathlib import Path

# Add app directory to sys.path
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import md_engine
from tests.test_helpers import IsolatedEnvironmentTestCase


class TestSlugify(unittest.TestCase):
    """Test slugify function for generating URL-safe and anchor-safe identifiers."""

    def test_basic_slugs(self):
        self.assertEqual(md_engine.slugify("Mi Primer Documento"), "mi-primer-documento")
        self.assertEqual(md_engine.slugify("Hello World 123"), "hello-world-123")

    def test_accents_and_diacritics(self):
        self.assertEqual(
            md_engine.slugify("Árboles, Niños, Canción y Pingüinos"),
            "arboles-ninos-cancion-y-pinguinos"
        )

    def test_punctuation_and_special_symbols(self):
        self.assertEqual(
            md_engine.slugify("Reporte 2026: ¿Éxito o Fallo? (100% / $0)"),
            "reporte-2026-exito-o-fallo-100-0"
        )

    def test_consecutive_spaces_and_hyphens(self):
        self.assertEqual(md_engine.slugify("Test   ---   Document"), "test-document")

    def test_fallback_on_empty_or_symbols(self):
        self.assertEqual(md_engine.slugify(""), "documento")
        self.assertEqual(md_engine.slugify("!@#$%^&*()"), "documento")


class TestCleanMarkdownInline(unittest.TestCase):
    """Test cleaning inline markdown elements to extract plain text titles."""

    def test_strips_html_tags(self):
        self.assertEqual(
            md_engine.clean_markdown_inline("<span class='badge'>Beta</span> Sistema"),
            "Beta Sistema"
        )

    def test_strips_inline_code(self):
        self.assertEqual(
            md_engine.clean_markdown_inline("Función `run_test()` en Python"),
            "Función run_test() en Python"
        )

    def test_strips_links_and_images(self):
        self.assertEqual(
            md_engine.clean_markdown_inline("Ver [Documentación](https://example.com) aquí"),
            "Ver Documentación aquí"
        )
        self.assertEqual(
            md_engine.clean_markdown_inline("![Icono](icon.png) Título Principal"),
            "Icono Título Principal"
        )

    def test_strips_bold_italic_strikethrough(self):
        self.assertEqual(
            md_engine.clean_markdown_inline("**Negrita** y *cursiva* y ~~tachado~~"),
            "Negrita y cursiva y tachado"
        )

    def test_strips_status_badges(self):
        self.assertEqual(
            md_engine.clean_markdown_inline("[PASS] Módulo de Autenticación"),
            "Módulo de Autenticación"
        )
        self.assertEqual(
            md_engine.clean_markdown_inline("Pruebas Unitarias [FAIL]"),
            "Pruebas Unitarias"
        )

    def test_strips_leading_markdown_prefixes(self):
        self.assertEqual(md_engine.clean_markdown_inline("### --- Título"), "Título")
        self.assertEqual(md_engine.clean_markdown_inline("- * Elemento"), "Elemento")


class TestSmartTitleDetection(unittest.TestCase):
    """Test heuristic and hierarchical title detection."""

    def test_custom_title_highest_priority(self):
        lines = ["# Título en H1", "Contenido"]
        title, src, idx = md_engine.detect_smart_title(lines, custom_title="Título Personalizado")
        self.assertEqual(title, "Título Personalizado")
        self.assertEqual(src, "custom")

    def test_frontmatter_priority(self):
        lines = ["# Título en H1"]
        fm = {"title": "Título desde YAML"}
        title, src, _ = md_engine.detect_smart_title(lines, frontmatter=fm)
        self.assertEqual(title, "Título desde YAML")
        self.assertEqual(src, "frontmatter")

    def test_explicit_h1_detection(self):
        lines = ["", "# Arquitectura del Sistema", "Introducción al proyecto"]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertEqual(title, "Arquitectura del Sistema")
        self.assertEqual(src, "h1")
        self.assertEqual(idx, 1)

    def test_setext_h1_detection(self):
        lines = ["Título Setext Nivel 1", "=====================", "Párrafo siguiente"]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertEqual(title, "Título Setext Nivel 1")
        self.assertEqual(src, "setext_h1")
        self.assertEqual(idx, 0)

    def test_h2_when_no_h1(self):
        lines = ["## Subtítulo Relevante", "Contenido del módulo"]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertEqual(title, "Subtítulo Relevante")
        self.assertEqual(src, "h2")

    def test_setext_h2_when_no_h1(self):
        lines = ["Subtítulo Setext Nivel 2", "------------------------", "Cuerpo"]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertEqual(title, "Subtítulo Setext Nivel 2")
        self.assertEqual(src, "setext_h2")

    def test_h3_when_no_h1_or_h2(self):
        lines = ["### Subsección Específica", "Detalle técnico"]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertEqual(title, "Subsección Específica")
        self.assertEqual(src, "h3")

    def test_file_stem_when_no_headers(self):
        lines = ["Párrafo inicial sin ningún encabezado ni formato."]
        title, src, _ = md_engine.detect_smart_title(lines, input_file_path="C:/docs/reporte_mensual_qa.md")
        self.assertEqual(title, "Reporte Mensual Qa")
        self.assertEqual(src, "file_stem")

    def test_bold_line_detection(self):
        lines = ["**Resumen Ejecutivo de Auditoría**", "Texto descriptivo..."]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertEqual(title, "Resumen Ejecutivo de Auditoría")
        self.assertEqual(src, "bold_line")

    def test_first_line_detection(self):
        lines = ["Documento sin encabezados ni formato explicito pero con texto largo."]
        title, src, idx = md_engine.detect_smart_title(lines)
        self.assertIn("Documento sin encabezados", title)
        self.assertEqual(src, "first_line")

    def test_fallback_when_empty(self):
        lines = ["", "   "]
        title, src, _ = md_engine.detect_smart_title(lines)
        self.assertTrue(title.startswith("Documento Markdown"))
        self.assertEqual(src, "fallback")


class TestStatusBadges(unittest.TestCase):
    """Test inline status badge rendering with Apple HIG styling."""

    def test_success_badges(self):
        for tag in ["[PASS]", "[PASSED]", "[OK]", "[APROBADO]", "[EXITOSO]"]:
            rendered = md_engine.format_status_badges(f"Estado: {tag}")
            self.assertIn('badge-success', rendered)

    def test_danger_badges(self):
        for tag in ["[FAIL]", "[FAILED]", "[ERROR]", "[FALLO]", "[REPROBADO]"]:
            rendered = md_engine.format_status_badges(f"Estado: {tag}")
            self.assertIn('badge-danger', rendered)

    def test_warning_badges(self):
        for tag in ["[WARN]", "[WARNING]", "[ADVERTENCIA]", "[PENDIENTE]"]:
            rendered = md_engine.format_status_badges(f"Estado: {tag}")
            self.assertIn('badge-warning', rendered)

    def test_info_badges(self):
        for tag in ["[INFO]", "[NOTA]", "[RECOMENDADO]"]:
            rendered = md_engine.format_status_badges(f"Estado: {tag}")
            self.assertIn('badge-info', rendered)


class TestInlineFormatting(unittest.TestCase):
    """Test inline Markdown transformations."""

    def test_inline_code_preserves_special_characters(self):
        text = "Ejecutar `def test_func(x < 5 & y > 2):` en consola"
        res = md_engine.inline_formatting(text)
        self.assertIn("<code>def test_func(x &lt; 5 &amp; y &gt; 2):</code>", res)

    def test_bold_and_italics(self):
        text = "Texto con **negrita**, __negrita2__, *cursiva* y _cursiva2_"
        res = md_engine.inline_formatting(text)
        self.assertIn("<strong>negrita</strong>", res)
        self.assertIn("<strong>negrita2</strong>", res)
        self.assertIn("<em>cursiva</em>", res)
        self.assertIn("<em>cursiva2</em>", res)

    def test_strikethrough(self):
        text = "Texto con ~~tachado~~"
        res = md_engine.inline_formatting(text)
        self.assertIn("<del>tachado</del>", res)

    def test_external_links_have_secure_attributes(self):
        text = "Visita [Google](https://www.google.com)"
        res = md_engine.inline_formatting(text)
        self.assertIn('href="https://www.google.com"', res)
        self.assertIn('target="_blank"', res)
        self.assertIn('rel="noopener noreferrer"', res)

    def test_anchor_links_are_slugified_locally(self):
        text = "Ir a [Sección de Pruebas](#Sección de Pruebas)"
        res = md_engine.inline_formatting(text)
        self.assertIn('href="#seccion-de-pruebas"', res)
        self.assertNotIn('target="_blank"', res)

    def test_image_rendering(self):
        text = "![Diagrama de Arquitectura](assets/arch.png)"
        res = md_engine.inline_formatting(text)
        self.assertIn('<img src="assets/arch.png"', res)
        self.assertIn('alt="Diagrama de Arquitectura"', res)

    def test_keyboard_shortcuts(self):
        text = "Presiona [[kbd:Ctrl+Shift+P]] para abrir comandos"
        res = md_engine.inline_formatting(text)
        self.assertIn("<kbd>Ctrl+Shift+P</kbd>", res)


class TestCodeBlocksAndSyntaxHighlighting(unittest.TestCase):
    """Test syntax highlighting and code block containers."""

    def test_python_syntax_highlighting(self):
        code = "def calcular(total):\n    return total * 1.16"
        res = md_engine.highlight_code_block(code, "python")
        self.assertIn('<span class="tok-kw">def</span>', res)
        self.assertIn('<span class="tok-kw">return</span>', res)

    def test_javascript_syntax_highlighting(self):
        code = "async function fetchData() {\n    const res = await fetch('/api');\n}"
        res = md_engine.highlight_code_block(code, "javascript")
        self.assertIn('<span class="tok-kw">async</span>', res)
        self.assertIn('<span class="tok-kw">function</span>', res)
        self.assertIn('<span class="tok-kw">const</span>', res)
        self.assertIn('<span class="tok-kw">await</span>', res)

    def test_diff_syntax_highlighting(self):
        diff = "+ linea agregada\n- linea eliminada\n  linea normal"
        res = md_engine.highlight_code_block(diff, "diff")
        self.assertIn('<span class="tok-diff-add">+ linea agregada</span>', res)
        self.assertIn('<span class="tok-diff-del">- linea eliminada</span>', res)
        self.assertIn('linea normal', res)

    def test_powershell_syntax_highlighting(self):
        ps = "param($Path)\nforeach ($f in $files) {\n    return $f\n}"
        res = md_engine.highlight_code_block(ps, "powershell")
        self.assertIn('<span class="tok-kw">param</span>', res)
        self.assertIn('<span class="tok-kw">foreach</span>', res)
        self.assertIn('<span class="tok-kw">return</span>', res)


class TestCalloutAlerts(unittest.TestCase):
    """Test GitHub & Apple HIG callout containers with SVG icons."""

    def test_all_alert_types(self):
        alerts = [
            ("NOTE", "alert-note"),
            ("TIP", "alert-tip"),
            ("IMPORTANT", "alert-important"),
            ("WARNING", "alert-warning"),
            ("CAUTION", "alert-caution")
        ]
        for alert_name, expected_class in alerts:
            md = f"> [!{alert_name}]\n> Este es un mensaje de prueba para {alert_name}."
            html = md_engine.compile_markdown_to_body(md)
            self.assertIn(expected_class, html)
            self.assertIn("<svg", html)
            self.assertIn(f"Este es un mensaje de prueba para {alert_name}", html)


class TestTables(unittest.TestCase):
    """Test responsive table compilation and alignment."""

    def test_table_with_alignment(self):
        md = """
| Columna 1 | Columna 2 | Columna 3 |
| :--- | :---: | ---: |
| Izquierda | Centro | Derecha |
| Val A | Val B | Val C |
"""
        html = md_engine.compile_markdown_to_body(md)
        self.assertIn('<div class="table-container">', html)
        self.assertIn('<table>', html)
        self.assertIn('>Columna 1</th>', html)
        self.assertIn('text-align: left;', html)
        self.assertIn('text-align: center;', html)
        self.assertIn('text-align: right;', html)


class TestListHierarchy(unittest.TestCase):
    """Test ordered, unordered, nested, and checklist hierarchy."""

    def test_nested_ordered_and_unordered_lists(self):
        md = """# Guía de Pasos
1. Paso Principal 1
2. Paso Principal 2
   - Subpaso A
   - Subpaso B
     1. Detalle B.1
3. Paso Principal 3
"""
        html = md_engine.compile_markdown_to_body(md)
        self.assertIn("<ol>", html)
        self.assertIn("<li>Paso Principal 1", html)
        self.assertIn("<li>Paso Principal 2", html)
        self.assertIn("<ul>", html)
        self.assertIn("Subpaso A", html)
        self.assertIn("Subpaso B", html)
        self.assertIn("Detalle B.1", html)

    def test_task_lists(self):
        md = """# Lista de Tareas
- [x] Tarea Completada
- [ ] Tarea Pendiente
  - [x] Subtarea Completada
"""
        html = md_engine.compile_markdown_to_body(md)
        self.assertIn('class="task-list"', html)
        self.assertIn('checked disabled', html)
        self.assertIn('type="checkbox" disabled', html)
        self.assertIn('Tarea Completada', html)
        self.assertIn('Tarea Pendiente', html)
        self.assertIn('Subtarea Completada', html)


class TestCatalogAndNavigation(IsolatedEnvironmentTestCase):
    """Integration test for full conversion, cross-navigation, index and latest generation."""

    def test_convert_and_update_library_creates_files(self):
        md1 = "# Primer Documento\nContenido de prueba número 1."
        res1 = md_engine.convert_and_update_library(md1, str(self.test_root), "Doc 1")
        self.assertTrue(res1["success"])
        self.assertTrue(Path(res1["file_path"]).exists())
        self.assertEqual(res1["title"], "Doc 1")

        # Give slight delay for file timestamp separation
        time.sleep(0.05)

        md2 = "# Segundo Documento\nContenido de prueba número 2."
        res2 = md_engine.convert_and_update_library(md2, str(self.test_root), "Doc 2")
        self.assertTrue(res2["success"])
        self.assertTrue(Path(res2["file_path"]).exists())
        self.assertEqual(res2["title"], "Doc 2")

        # Verify cross-document navigation in generated HTML
        with open(res1["file_path"], "r", encoding="utf-8") as f:
            h1 = f.read()
        self.assertIn('class="top-nav-bar"', h1)
        self.assertIn('href="./index.html"', h1)
        self.assertIn('href="./latest.html"', h1)

        # Verify index.html existence and reverse chronological sort order
        index_file = self.test_root / "index.html"
        self.assertTrue(index_file.exists())
        with open(index_file, "r", encoding="utf-8") as f:
            idx_html = f.read()
        self.assertIn("Biblioteca de Documentos", idx_html)
        self.assertIn("Doc 1", idx_html)
        self.assertIn("Doc 2", idx_html)

        # Doc 2 is newest, must appear before Doc 1 in index
        pos_doc2 = idx_html.find("Doc 2")
        pos_doc1 = idx_html.find("Doc 1")
        self.assertLess(pos_doc2, pos_doc1, "Doc 2 debe aparecer antes de Doc 1 en el índice cronológico descendente")

        # Verify latest.html points to Doc 2
        latest_file = self.test_root / "latest.html"
        self.assertTrue(latest_file.exists())
        with open(latest_file, "r", encoding="utf-8") as f:
            latest_html = f.read()
        self.assertIn(res2["filename"], latest_html)


class TestTerracottaThemeDesignTokens(unittest.TestCase):
    """
    Verifica que el sistema de diseño Terracotta & Smoked Charcoal (Cobre Terracota Carbón Mate)
    esté correctamente estructurado en COMMON_STYLES y en las plantillas HTML compiladas.
    """

    def test_dark_mode_tokens(self):
        self.assertIn("--canvas-bg: #0b0a0a;", md_engine.COMMON_STYLES)
        self.assertIn("--card-bg: #141312;", md_engine.COMMON_STYLES)
        self.assertIn("--card-alt-bg: #1c1a19;", md_engine.COMMON_STYLES)
        self.assertIn("--primary: #d97736;", md_engine.COMMON_STYLES)
        self.assertIn("--primary-hover: #e58746;", md_engine.COMMON_STYLES)
        self.assertIn("--text-main: #f5ede6;", md_engine.COMMON_STYLES)
        self.assertIn("--text-muted: #a6988f;", md_engine.COMMON_STYLES)
        self.assertIn("--success-badge-text: #48bb78;", md_engine.COMMON_STYLES)

    def test_light_mode_terracotta_tokens(self):
        self.assertIn("html.light {", md_engine.COMMON_STYLES)
        self.assertIn("--canvas-bg: #f9f6f3;", md_engine.COMMON_STYLES)
        self.assertIn("--primary: #b85b1e;", md_engine.COMMON_STYLES)
        self.assertIn("--primary-hover: #d97736;", md_engine.COMMON_STYLES)
        self.assertIn("--text-main: #231f1c;", md_engine.COMMON_STYLES)

    def test_favicon_stroke_color(self):
        self.assertIn("stroke='%23d97736'", md_engine.HTML_DOC_TEMPLATE)


if __name__ == "__main__":
    unittest.main()
