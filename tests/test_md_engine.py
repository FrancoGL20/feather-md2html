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
import shutil
import tempfile
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

    def test_table_without_separator_or_gherkin(self):
        """Test tables without explicit :--- separator line (e.g. Gherkin data tables)."""
        md = """
| Usuario | Contraseña | Rol |
| admin | secret123 | superuser |
| guest | guestpass | viewer |
"""
        html = md_engine.compile_markdown_to_body(md)
        self.assertIn('<div class="table-container">', html)
        self.assertIn('<table>', html)
        self.assertIn('>Usuario</th>', html)
        self.assertIn('>admin</td>', html)
        self.assertIn('>superuser</td>', html)

    def test_single_line_pipe_and_math_pipe(self):
        """Test single-line pipe and mathematical pipes do not cause infinite loops and render as text."""
        md = """# Título de Prueba
Este es un texto con opción A | opción B.
Fórmula: |x| < 10.
| sólo una línea |"""
        html = md_engine.compile_markdown_to_body(md)
        self.assertIn('opción A | opción B', html)
        self.assertIn('|x| < 10', html)
        self.assertIn('| sólo una línea |', html)

    def test_indented_blockquote_and_hashtag(self):
        """Test indented blockquotes and hashtags do not cause infinite loops."""
        md = """  > Cita sangrada con espacios
#hashtag sin espacio
Texto normal."""
        html = md_engine.compile_markdown_to_body(md)
        self.assertIn('<blockquote><p>Cita sangrada con espacios</p></blockquote>', html)
        self.assertIn('#hashtag sin espacio', html)



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


class TestVolcanicAmberThemeDesignTokens(unittest.TestCase):
    """
    Verifica que el sistema de diseño Volcanic Amber & Deep Obsidian (Ámbar Volcánico y Negro Obsidiana)
    esté correctamente estructurado en COMMON_STYLES y en las plantillas HTML compiladas.
    """

    def test_dark_mode_tokens(self):
        self.assertIn("--canvas-bg: #070708;", md_engine.COMMON_STYLES)
        self.assertIn("--card-bg: #111114;", md_engine.COMMON_STYLES)
        self.assertIn("--card-alt-bg: #17181c;", md_engine.COMMON_STYLES)
        self.assertIn("--primary: #f97316;", md_engine.COMMON_STYLES)
        self.assertIn("--primary-hover: #fb923c;", md_engine.COMMON_STYLES)
        self.assertIn("--text-main: #f8fafc;", md_engine.COMMON_STYLES)
        self.assertIn("--text-muted: #94a3b8;", md_engine.COMMON_STYLES)
        self.assertIn("--success-badge-text: #10b981;", md_engine.COMMON_STYLES)

    def test_light_mode_volcanic_amber_tokens(self):
        self.assertIn("html.light {", md_engine.COMMON_STYLES)
        self.assertIn("--canvas-bg: #f8fafc;", md_engine.COMMON_STYLES)
        self.assertIn("--primary: #c2410c;", md_engine.COMMON_STYLES)
        self.assertIn("--primary-hover: #ea580c;", md_engine.COMMON_STYLES)
        self.assertIn("--text-main: #0f172a;", md_engine.COMMON_STYLES)

    def test_favicon_stroke_color(self):
        self.assertIn("stroke='%23f97316'", md_engine.HTML_DOC_TEMPLATE)


class TestMermaidDiagrams(IsolatedEnvironmentTestCase):
    """
    Suite de pruebas exhaustiva para el soporte de Diagramas Mermaid 100% Offline e Interactivos.
    Verifica:
    1. Parseo léxico y sintáctico de bloques ```mermaid.
    2. Generación de tarjeta interactiva Apple HIG con botones "Ver código" y "Copiar".
    3. Inyección autónoma del runtime de Mermaid embebido sin llamadas externas ni CDNs.
    4. Omisión del script de Mermaid en documentos sin diagramas (Zero-Bloatware).
    5. Asignación secuencial de identificadores únicos para múltiples diagramas.
    6. Seguridad contra inyecciones XSS dentro de los nodos y etiquetas del diagrama.
    7. Estilos de diseño, tokens de color y reglas de impresión en COMMON_STYLES.
    """

    def test_mermaid_block_parsing_and_card_structure(self):
        md = "```mermaid\ngraph TD\n  A[Inicio] --> B[Fin]\n```"
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_mermaid"])
        body = parsed["body"]
        self.assertIn('class="mermaid-block" id="block-mermaid-1"', body)
        self.assertIn('class="mermaid-header"', body)
        self.assertIn('<span>Diagrama Mermaid</span>', body)
        self.assertIn("toggleMermaidSource('mermaid-1', this)", body)
        self.assertIn("copyMermaidSource('mermaid-1', this)", body)
        self.assertIn('id="render-mermaid-1"', body)
        self.assertIn('id="source-mermaid-1"', body)
        self.assertIn('id="raw-mermaid-1"', body)
        self.assertIn('style="display: none;"', body)
        self.assertIn('A[Inicio] --&gt; B[Fin]', body)

    def test_multiple_mermaid_blocks_sequential_ids(self):
        md = """# Documento con Múltiples Diagramas

```mermaid
graph TD
  A --> B
```

Texto intermedio explicativo.

```mermaid
sequenceDiagram
  Alice->>Bob: Hola
```
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_mermaid"])
        body = parsed["body"]
        self.assertIn('id="block-mermaid-1"', body)
        self.assertIn('id="block-mermaid-2"', body)
        self.assertIn("toggleMermaidSource('mermaid-1', this)", body)
        self.assertIn("toggleMermaidSource('mermaid-2', this)", body)
        self.assertIn('id="render-mermaid-1"', body)
        self.assertIn('id="render-mermaid-2"', body)
        self.assertIn('id="raw-mermaid-1"', body)
        self.assertIn('id="raw-mermaid-2"', body)

    def test_standard_code_blocks_unaffected(self):
        md = "```python\ndef test():\n    return 42\n```"
        parsed = md_engine.parse_markdown(md)
        self.assertFalse(parsed["has_mermaid"])
        body = parsed["body"]
        self.assertNotIn("mermaid-block", body)
        self.assertIn('class="code-block"', body)
        self.assertIn("<span>PYTHON</span>", body)

    def test_mermaid_runtime_inlined_offline_when_present(self):
        md = "# Arquitectura de Sistema\n\n```mermaid\ngraph LR\n  Client --> Server\n```"
        res = md_engine.convert_and_update_library(md, str(self.test_root), "Doc Con Diagrama")
        self.assertTrue(res["success"])
        html_path = Path(res["file_path"])
        self.assertTrue(html_path.exists())

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verifica runtime y funciones cliente inyectadas
        self.assertIn("renderMermaidDiagrams", content)
        self.assertIn("toggleMermaidSource", content)
        self.assertIn("copyMermaidSource", content)
        self.assertIn("mermaid.initialize", content)
        # Verifica sincronización con alternador de tema
        self.assertIn("if (typeof renderMermaidDiagrams === 'function')", content)
        # Verifica ausencia total de dependencias remotas / CDNs (Zero-Bloatware / 100% Offline)
        self.assertNotIn("cdn.jsdelivr.net", content)
        self.assertNotIn("unpkg.com", content)
        self.assertNotIn("cdnjs.cloudflare.com", content)

    def test_mermaid_runtime_omitted_when_no_diagrams(self):
        md = "# Documento Regular\n\nEste documento no tiene diagramas mermaid, solo texto y listas.\n- Item 1\n- Item 2"
        res = md_engine.convert_and_update_library(md, str(self.test_root), "Doc Sin Diagrama")
        self.assertTrue(res["success"])
        html_path = Path(res["file_path"])

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # El runtime y controladores pesados no deben inyectarse
        self.assertNotIn("mermaid.initialize", content)
        self.assertNotIn("toggleMermaidSource", content)
        # El documento debe ser ligero (< 50 KB)
        self.assertLess(html_path.stat().st_size, 50000)

    def test_mermaid_xss_protection(self):
        md = "```mermaid\ngraph TD\n  A[\"<script>alert('xss')</script>\"] --> B\n```"
        compiled_body = md_engine.compile_markdown_to_body(md)
        self.assertNotIn("<script>", compiled_body)
        self.assertIn("&lt;script&gt;", compiled_body)

    def test_mermaid_css_styles_and_print_rules(self):
        self.assertIn(".mermaid-block {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-header {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-title {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-actions {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-render {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-source {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-error {", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-loading {", md_engine.COMMON_STYLES)
        # Print media query
        self.assertIn(".mermaid-actions { display: none !important; }", md_engine.COMMON_STYLES)
        self.assertIn(".mermaid-source { display: none !important; }", md_engine.COMMON_STYLES)


class TestIndexMetadataCaching(unittest.TestCase):
    """Pruebas unitarias para el sistema de caché de metadatos y aceleración de índice."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cache_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_metadata_cache_persists_and_avoids_reread(self):
        f = self.temp_dir / "doc1.html"
        f.write_text("<!DOCTYPE html><html><head><title>Título Original</title></head><body>Hola</body></html>", encoding="utf-8")

        # Primera generación: extrae de disco y crea .index_cache.json
        md_engine.generate_index_html(self.temp_dir)
        cache_file = self.temp_dir / ".index_cache.json"
        self.assertTrue(cache_file.exists())
        
        cache = md_engine.load_index_cache(self.temp_dir)
        self.assertIn("doc1.html", cache)
        self.assertEqual(cache["doc1.html"]["title"], "Título Original")

        # Sobrescribimos el caché con un título artificial sin tocar el archivo físico ni su mtime
        cache["doc1.html"]["title"] = "Título En Caché Rápido"
        md_engine.save_index_cache(self.temp_dir, cache)

        # Segunda generación: debe respetar el título del caché sin abrir el archivo físico
        index_file = md_engine.generate_index_html(self.temp_dir)
        content = index_file.read_text(encoding="utf-8")
        self.assertIn("Título En Caché Rápido", content)

    def test_generate_index_html_uses_known_titles_without_reading_disk(self):
        f = self.temp_dir / "doc2.html"
        f.write_text("<!DOCTYPE html><html><head><title>Título En Disco</title></head><body>Hola</body></html>", encoding="utf-8")

        # Invocamos con known_titles
        index_file = md_engine.generate_index_html(self.temp_dir, known_titles={"doc2.html": "Título Provisto Directamente"})
        content = index_file.read_text(encoding="utf-8")
        self.assertIn("Título Provisto Directamente", content)

        cache = md_engine.load_index_cache(self.temp_dir)
        self.assertEqual(cache["doc2.html"]["title"], "Título Provisto Directamente")

    def test_remove_from_index_cache_cleans_entry(self):
        f = self.temp_dir / "doc3.html"
        f.write_text("<title>Doc 3</title>", encoding="utf-8")
        md_engine.generate_index_html(self.temp_dir)

        cache = md_engine.load_index_cache(self.temp_dir)
        self.assertIn("doc3.html", cache)

        md_engine.remove_from_index_cache(self.temp_dir, "doc3.html")
        cache_after = md_engine.load_index_cache(self.temp_dir)
        self.assertNotIn("doc3.html", cache_after)


class TestLatexMathRendering(IsolatedEnvironmentTestCase):
    """
    Suite de pruebas exhaustiva para el soporte y renderizado nativo de fórmulas
    matemáticas LaTeX (Display Math $$...$$ e Inline Math $...$).
    Valida:
    1. Parseo correcto de fórmulas de bloque y en línea del usuario.
    2. Preservación intacta de subíndices (_) y asteriscos (*) sin interferencia de Markdown.
    3. Protección contra signos de dólar monetarios y escapados ($50 USD, \\$12,000,000).
    4. Soporte para bloques multilínea y bloques de código ```math.
    5. Inmunidad del detector de títulos inteligentes frente a fórmulas al inicio.
    6. Inyección autónoma del runtime MathJax 3 100% offline (sin CDNs).
    7. Omisión total de scripts en documentos sin matemáticas (Zero-Bloatware).
    8. Estilos CSS de alta definición para .math-block y .math-inline.
    """

    def test_user_examples_block_and_inline(self):
        md = r"""# Reporte Financiero

$$\text{Rate Per Unit} = 9,999,999 \quad \text{y} \quad \text{Base Charge} = 2,000,001 \quad \Longrightarrow \quad \text{Total Liquidado} = \$12,000,000 \text{ COP}$$

El valor liquidado fue $\text{Valor AR} = \text{Flete Pactado Base} + \text{Intermediación EDINSA (\%)}$.
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_math"])
        body = parsed["body"]

        # Bloque matemático
        self.assertIn('class="math-block" id="math-block-1"', body)
        self.assertIn(r"\text{Rate Per Unit} = 9,999,999 \quad \text{y}", body)
        self.assertIn(r"\Longrightarrow \quad \text{Total Liquidado} = \$12,000,000 \text{ COP}", body)

        # Fórmula en línea
        self.assertIn('class="math-inline"', body)
        self.assertIn(r"$\text{Valor AR} = \text{Flete Pactado Base} + \text{Intermediación EDINSA (\%)}$", body)

    def test_subscripts_and_multiplication_not_mangled_by_markdown(self):
        md = r"""# Álgebra
Fórmula con subíndices: $x_1 + x_2 = y_{total}$.
Fórmula con multiplicación: $a * b * c = d$.
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_math"])
        body = parsed["body"]

        # No debe haber etiquetas <em> dentro de las variables
        self.assertNotIn("x<em>", body)
        self.assertNotIn("y</em>", body)
        self.assertIn(r"$x_1 + x_2 = y_{total}$", body)
        self.assertIn(r"$a * b * c = d$", body)

    def test_currency_defense_dollars_preserved(self):
        md = r"""# Presupuesto
El costo es $50 USD y el otro es $100 USD.
Precio neto: \$12,000,000 COP.
"""
        parsed = md_engine.parse_markdown(md)
        body = parsed["body"]

        # No debe clasificar montos de moneda ordinarios como matemáticas
        self.assertNotIn('class="math-inline"', body)
        self.assertNotIn('class="math-block"', body)
        self.assertIn("$50 USD y el otro es $100 USD.", body)

    def test_multiline_display_math(self):
        md = r"""# Ecuaciones de Maxwell
$$
\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0} \\
\nabla \cdot \mathbf{B} = 0
$$
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_math"])
        body = parsed["body"]

        self.assertIn('class="math-block" id="math-block-1"', body)
        self.assertIn(r"\nabla \cdot \mathbf{E}", body)
        self.assertIn(r"\nabla \cdot \mathbf{B} = 0", body)

    def test_fenced_code_block_math(self):
        md = """# Cálculo
```math
\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
```
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_math"])
        body = parsed["body"]

        self.assertIn('class="math-block" id="math-block-1"', body)
        self.assertIn(r"\int_{0}^{\infty}", body)

    def test_smart_title_does_not_steal_math_formula(self):
        md = r"""$$\text{Rate Per Unit} = 9,999,999 \quad \text{y} \quad \text{Base Charge} = 2,000,001 \quad \Longrightarrow \quad \text{Total Liquidado} = \$12,000,000 \text{ COP}$$

$\text{Valor AR} = \text{Flete Pactado Base} + \text{Intermediación EDINSA (\%)}$
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_math"])
        # El título no debe ser la fórmula ni un token
        self.assertNotIn(r"\text{Rate Per Unit}", parsed["title"])
        self.assertNotIn("MATH", parsed["title"])
        # Ambas fórmulas deben estar en el cuerpo
        self.assertIn('class="math-block"', parsed["body"])
        self.assertIn('class="math-inline"', parsed["body"])

    def test_bracket_and_parentheses_delimiters(self):
        md = r"""# Notación TeX Alternativa
Ecuación en corchetes: \[ E = mc^2 \]
Ecuación en paréntesis: \( e^{i\pi} + 1 = 0 \)
"""
        parsed = md_engine.parse_markdown(md)
        self.assertTrue(parsed["has_math"])
        body = parsed["body"]

        self.assertIn('class="math-block"', body)
        self.assertIn(r"E = mc^2", body)
        self.assertIn('class="math-inline"', body)
        self.assertIn(r"e^{i\pi} + 1 = 0", body)

    def test_mathjax_runtime_inlined_offline_when_present(self):
        md = r"""# Documento Con Fórmulas
$$\text{Total} = 100$$
"""
        res = md_engine.convert_and_update_library(md, str(self.test_root), "Doc Con Matematicas")
        self.assertTrue(res["success"])
        html_path = Path(res["file_path"])
        self.assertTrue(html_path.exists())

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verifica configuración y runtime inyectados
        self.assertIn("window.MathJax", content)
        self.assertIn("inlineMath", content)
        self.assertIn("displayMath", content)
        # Verifica ausencia total de llamadas a CDNs y scripts remotos (Zero-Bloatware / 100% Offline)
        self.assertNotIn('<script src="http', content)
        self.assertNotIn('<link rel="stylesheet" href="http', content)
        self.assertNotIn('src="https://cdn.jsdelivr.net', content)
        self.assertNotIn('src="https://cdnjs.cloudflare.com', content)
        self.assertNotIn('src="https://unpkg.com', content)

    def test_mathjax_runtime_omitted_when_no_math_zero_bloatware(self):
        md = """# Documento Regular
Este documento no contiene fórmulas matemáticas.
- Item 1
- Item 2
"""
        res = md_engine.convert_and_update_library(md, str(self.test_root), "Doc Sin Matematicas")
        self.assertTrue(res["success"])
        html_path = Path(res["file_path"])

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # MathJax no debe inyectarse
        self.assertNotIn("window.MathJax", content)
        # Archivo debe ser ligero (< 50 KB)
        self.assertLess(html_path.stat().st_size, 50000)

    def test_math_css_styles_and_print_rules(self):
        self.assertIn(".math-block {", md_engine.COMMON_STYLES)
        self.assertIn(".math-inline {", md_engine.COMMON_STYLES)
        self.assertIn("mjx-container[jax=\"SVG\"]", md_engine.COMMON_STYLES)
        # Regla de impresión
        self.assertIn("background: transparent !important;", md_engine.COMMON_STYLES)


if __name__ == "__main__":
    unittest.main()

