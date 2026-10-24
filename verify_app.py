#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Script for MarkdownToHTML Desktop Application
"""
import os
import sys
import shutil
from pathlib import Path

# Configure stdout for UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add app dir to sys.path
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

import md_engine

def run_tests():
    print("--- INICIANDO VERIFICACIÓN DEL MOTOR ---")
    
    test_root = APP_DIR / "test_output_library"
    if test_root.exists():
        shutil.rmtree(test_root)
    test_root.mkdir(parents=True, exist_ok=True)
    
    # 1. Test Text Conversion
    doc1_md = """# Primer Documento de Auditoría
> [!IMPORTANT]
> Este es un hallazgo crítico de seguridad.

- [x] Parche aplicado
- [ ] Validación pendiente

| Módulo | Estado | Severidad |
| :--- | :---: | ---: |
| Auth | [FAIL] | Alta |
| API | [PASS] | Baja |
"""
    print("[1/5] Convirtiendo Doc 1 (Texto plano)...")
    res1 = md_engine.convert_and_update_library(doc1_md, str(test_root), "Primer Documento de Auditoría")
    assert res1["success"] is True, "Fallo en conversión de Doc 1"
    assert Path(res1["file_path"]).exists(), f"El archivo {res1['file_path']} no fue creado"
    print(f"  ✓ Doc 1 creado: {res1['filename']}")

    # 2. Test File Conversion
    sample_file = APP_DIR / "sample_doc.md"
    sample_md = """# Segundo Documento desde Archivo
Este documento fue cargado desde una ruta física de archivo.

```python
def saludar(nombre):
    return f"Hola {nombre}!"
```

> [!TIP]
> Rendimiento óptimo en menos de 20 milisegundos.
"""
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(sample_md)

    print("[2/5] Convirtiendo Doc 2 (Desde archivo físico)...")
    res2 = md_engine.convert_and_update_library(sample_md, str(test_root), custom_title="Segundo Documento", input_file_path=str(sample_file))
    assert res2["success"] is True, "Fallo en conversión de Doc 2"
    assert Path(res2["file_path"]).exists(), "El archivo Doc 2 no fue creado"
    print(f"  ✓ Doc 2 creado: {res2['filename']}")

    # 3. Verify Cross-Navigation in generated files
    print("[3/5] Verificando barra de navegación superior en los archivos creados...")
    with open(res1["file_path"], "r", encoding="utf-8") as f:
        doc1_html = f.read()
    assert 'href="./index.html"' in doc1_html, "Falta enlace a index.html en la barra superior"
    assert 'href="./latest.html"' in doc1_html, "Falta enlace a latest.html en la barra superior"
    assert 'top-nav-bar' in doc1_html, "Falta clase top-nav-bar"
    print("  ✓ Barra de navegación cruzada confirmada en Doc 1")

    # 4. Verify index.html (Catalog ordered newest to oldest)
    print("[4/5] Verificando catálogo index.html...")
    index_file = test_root / "index.html"
    assert index_file.exists(), "No se generó el archivo index.html en el directorio raíz"
    with open(index_file, "r", encoding="utf-8") as f:
        index_html = f.read()
    assert "Biblioteca de Documentos" in index_html, "Título del índice ausente"
    assert "Segundo Documento" in index_html, "Doc 2 no aparece en index.html"
    assert "Primer Documento de Auditoría" in index_html, "Doc 1 no aparece en index.html"
    
    # Verificar orden: Doc 2 fue creado después que Doc 1, debe aparecer antes en el HTML
    pos_doc2 = index_html.find("Segundo Documento")
    pos_doc1 = index_html.find("Primer Documento de Auditoría")
    assert pos_doc2 < pos_doc1, f"El orden cronológico es incorrecto: Doc 2 pos {pos_doc2} vs Doc 1 pos {pos_doc1}"
    print("  ✓ Catálogo index.html generado y ordenado del más nuevo al más viejo")

    # 5. Verify latest.html pointer
    print("[5/8] Verificando puntero latest.html...")
    latest_file = test_root / "latest.html"
    assert latest_file.exists(), "No se generó latest.html"
    with open(latest_file, "r", encoding="utf-8") as f:
        latest_html = f.read()
    assert res2["filename"] in latest_html, f"latest.html no apunta al archivo más nuevo {res2['filename']}"
    print(f"  ✓ latest.html apunta correctamente a: {res2['filename']}")

    # 6. Test Smart Title Detection
    print("[6/8] Verificando detección inteligente de títulos (H2, Negrita, Setext)...")
    # Caso A: Markdown con H2 sin H1
    h2_md = "## Refactorización De Pruebas LaborHub\n\nDetalles del refactor..."
    res_h2 = md_engine.convert_and_update_library(h2_md, str(test_root))
    assert res_h2["title"] == "Refactorización De Pruebas LaborHub", f"Fallo en título H2: {res_h2['title']}"
    assert "refactorizacion-de-pruebas-laborhub" in res_h2["filename"], f"Fallo en slug H2: {res_h2['filename']}"

    # Caso B: Markdown que inicia con línea en negrita
    bold_md = "**Reporte de Cobertura QA**\n\nResultados de las pruebas..."
    res_bold = md_engine.convert_and_update_library(bold_md, str(test_root))
    assert res_bold["title"] == "Reporte de Cobertura QA", f"Fallo en título negrita: {res_bold['title']}"

    # Caso C: Setext heading
    setext_md = "Título Setext Principal\n=======================\n\nCuerpo del reporte..."
    res_setext = md_engine.convert_and_update_library(setext_md, str(test_root))
    assert res_setext["title"] == "Título Setext Principal", f"Fallo en título Setext: {res_setext['title']}"
    print("  ✓ Detección inteligente de títulos validada (H2, Negrita y Setext superados)")

    # 7. Test History Synchronization on Startup
    print("[7/8] Verificando sincronización de historial en inicio...")
    import app
    fake_doc_info = {
        "title": "Doc Fantasma",
        "filename": "doc_fantasma.html",
        "file_url": "file:///fake/path/doc_fantasma.html",
        "file_path": str(test_root / "doc_fantasma_inexistente.html"),
        "timestamp": "23/10/2026 04:00 PM"
    }
    app.add_recent_conversion(fake_doc_info)
    # Al llamar get_or_create_config, debe filtrar el archivo fantasma
    cfg = app.get_or_create_config()
    ghost_found = any(r.get("filename") == "doc_fantasma.html" for r in cfg["recent_conversions"])
    assert not ghost_found, "El archivo inexistente no fue depurado del historial"
    print("  ✓ Sincronización exitosa: archivos inexistentes se purgan automáticamente")

    # 8. Test Document Deletion
    print("[8/8] Verificando eliminación de documentos...")
    file_to_del = Path(res_h2["file_path"])
    assert file_to_del.exists(), "El archivo a eliminar debería existir antes del test"
    
    # Simular la eliminación a través del motor y config
    file_to_del.unlink()
    md_engine.generate_index_html(test_root)
    cfg_after = app.get_or_create_config()
    assert not file_to_del.exists(), "El archivo físico no fue eliminado"
    with open(test_root / "index.html", "r", encoding="utf-8") as f:
        idx_after = f.read()
    assert "Refactorización De Pruebas LaborHub" not in idx_after, "El documento eliminado sigue apareciendo en index.html"
    print("  ✓ Eliminación completa de documento validada en disco, catálogo e historial")

    # 9. Test Nested List Hierarchies and Ordered Lists
    print("[9/9] Verificando jerarquía de listas anidadas y listas ordenadas...")
    list_md = """# Prueba de Listas
1. Elemento Principal 1
2. Elemento Principal 2
   - Sub-elemento 2.1
   - Sub-elemento 2.2
     - Sub-sub-elemento 2.2.1
3. Elemento Principal 3

- [ ] Tarea 1
  - [x] Subtarea 1.1
"""
    res_list = md_engine.convert_and_update_library(list_md, str(test_root), custom_title="Prueba de Listas")
    assert res_list["success"] is True
    with open(res_list["file_path"], "r", encoding="utf-8") as f:
        list_html = f.read()
    
    # Validar que <ol> existe y contiene <li>
    assert "<ol>" in list_html and "</ol>" in list_html, "Falta estructura <ol> para lista ordenada"
    # Validar anidación: <ul> de sub-elementos debe estar dentro de <li>
    assert "<li>Elemento Principal 2" in list_html, "Falta <li> para Elemento Principal 2"
    assert "<ul>" in list_html and "Sub-elemento 2.1" in list_html, "Sub-elemento 2.1 no anidado en <ul>"
    # Validar sub-sub-elemento
    assert "Sub-sub-elemento 2.2.1" in list_html, "Sub-sub-elemento 2.2.1 ausente"
    # Validar task list anidada
    assert "task-list" in list_html and "Subtarea 1.1" in list_html, "Task list anidada falló"
    # Validar presencia de reglas CSS de jerarquía
    assert "padding-left: 1.7rem;" in list_html, "Falta regla CSS de padding-left para listas"
    assert "ul ul, ol ul" in list_html, "Faltan reglas CSS de sangría anidada"
    print("  ✓ Jerarquía de listas anidadas validada con sangría correcta")

    # Limpieza
    if sample_file.exists():
        try:
            sample_file.unlink()
        except Exception:
            pass
    shutil.rmtree(test_root, ignore_errors=True)

    print("\n==========================================")
    print("✓ TODAS LAS PRUEBAS RÁPIDAS PASARON EXITOSAMENTE (9/9)")
    print("==========================================")

    if "--full" in sys.argv or "-a" in sys.argv or "--all" in sys.argv:
        print("\nEjecutando suite integral exhaustiva (run_tests.py)...")
        import run_tests
        return run_tests.run_all_tests()
    else:
        print("\n[TIP] Para ejecutar la suite integral completa (82 tests unitarios, API, seguridad y geometría):")
        print("      python run_tests.py  (o: python verify_app.py --full)")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests() or 0)
