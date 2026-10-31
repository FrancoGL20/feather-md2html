#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library catalog use-case service.
Generates the chronological index.html catalog, updates the latest.html pointer,
and orchestrates safe document deletion.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from md2html.adapters.storage.index_cache import (
    extract_title_from_html,
    get_cached_title_or_read,
    load_index_cache,
    remove_from_index_cache,
    save_index_cache,
)
from md2html.core.compiler.inline_parser import escape
from md2html.templates.icons import ICON_BOLT, ICON_COPY, ICON_DOC, ICON_SEARCH
from md2html.templates.loader import (
    get_catalog_styles,
    get_catalog_template,
    get_common_styles,
    get_latest_redirect_template,
)


def generate_index_html(root_dir: Path, known_titles: Optional[Dict[str, str]] = None) -> Path:
    """
    Generates or updates index.html in root_dir ordered from newest to oldest.
    Uses .index_cache.json metadata to avoid reading unchanged HTML files.
    """
    known_titles = known_titles or {}
    cache = load_index_cache(root_dir)
    cache_dirty = False

    html_files = []
    for f in root_dir.glob("*.html"):
        if f.name.lower() in ("index.html", "latest.html"):
            continue
        try:
            stat = f.stat()
            mtime = stat.st_mtime
            size_kb = max(1, round(stat.st_size / 1024))

            if f.name in known_titles:
                doc_title = known_titles[f.name]
                cache[f.name] = {"title": doc_title, "mtime": mtime, "size_kb": size_kb}
                cache_dirty = True
            elif (
                f.name in cache
                and cache[f.name].get("mtime") == mtime
                and cache[f.name].get("size_kb") == size_kb
            ):
                doc_title = cache[f.name]["title"]
            else:
                doc_title = get_cached_title_or_read(f)
                cache[f.name] = {"title": doc_title, "mtime": mtime, "size_kb": size_kb}
                cache_dirty = True

            dt = datetime.fromtimestamp(mtime)
            html_files.append(
                {
                    "path": f,
                    "filename": f.name,
                    "title": doc_title,
                    "mtime": mtime,
                    "date_str": dt.strftime("%d/%m/%Y, %I:%M %p"),
                    "size_kb": size_kb,
                }
            )
        except Exception:
            continue

    if cache_dirty:
        save_index_cache(root_dir, cache)

    html_files.sort(key=lambda x: x["mtime"], reverse=True)

    items_html = []
    for doc in html_files:
        fn = escape(doc["filename"])
        ttl = escape(doc["title"])
        dt_s = escape(doc["date_str"])
        items_html.append(
            f"""
        <div class="doc-card" data-title="{ttl.lower()}" data-file="{fn.lower()}">
          <div class="doc-card-header">
            <div class="doc-card-title-group">
              <span class="doc-card-icon">{ICON_DOC}</span>
              <h2 class="doc-card-title"><a href="./{fn}">{ttl}</a></h2>
            </div>
            <span class="doc-card-date">📅 {dt_s}</span>
          </div>
          <div class="doc-card-meta">
            <code class="doc-card-slug">{fn}</code>
            <span class="doc-card-size">💾 {doc['size_kb']} KB</span>
          </div>
          <div class="doc-card-actions">
            <a href="./{fn}" class="doc-btn doc-btn-primary">{ICON_DOC} Abrir Documento</a>
            <button class="doc-btn doc-btn-secondary" onclick="copyDocLink('{fn}', this)">{ICON_COPY} <span>Copiar Enlace</span></button>
          </div>
        </div>
        """
        )

    cards_markup = (
        "".join(items_html)
        if items_html
        else """
    <div class="empty-state">
      <div class="empty-state-icon">📂</div>
      <h3>No hay documentos generados todavía</h3>
      <p>Genera tu primer documento desde la aplicación de escritorio y aparecerá listado aquí automáticamente.</p>
    </div>
    """
    )

    newest_link = f'./{html_files[0]["filename"]}' if html_files else "./index.html"

    template = get_catalog_template()
    index_content = template.format(
        common_styles=get_common_styles(),
        catalog_styles=get_catalog_styles(),
        newest_link=newest_link,
        icon_bolt=ICON_BOLT,
        doc_count=len(html_files),
        icon_search=ICON_SEARCH,
        cards_markup=cards_markup,
        root_dir_escaped=escape(str(root_dir)),
    )

    index_file = root_dir / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)
    return index_file


def generate_latest_redirect(root_dir: Path, newest_file: Path, doc_title: str) -> Path:
    """Generates latest.html with an immediate meta-refresh redirect to newest_file."""
    rel_name = newest_file.name
    template = get_latest_redirect_template()
    latest_content = template.format(
        rel_name=rel_name,
        common_styles=get_common_styles(),
        doc_title_escaped=escape(doc_title),
    )
    latest_file = root_dir / "latest.html"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(latest_content)
    return latest_file


def delete_document_from_library(
    root_dir: Path,
    filename: str,
    file_path_str: str,
    config: Dict[str, Any],
    save_config_fn: Callable[[Dict[str, Any]], None],
) -> Tuple[int, Dict[str, Any]]:
    """
    Safely deletes a generated HTML document from disk, updates recent_conversions,
    purges the index metadata cache, and regenerates index.html and latest.html.

    Returns:
        Tuple of (http_status_code, response_dict).
    """
    target_name = (file_path_str and Path(file_path_str).name) or filename
    if target_name.lower() in ("index.html", "latest.html") or (
        target_name and Path(target_name).suffix.lower() not in (".html", ".htm")
    ):
        return 400, {"error": "Archivo protegido o no permitido para eliminación."}

    target_file: Optional[Path] = None
    if file_path_str:
        p = Path(file_path_str).resolve()
        if p.exists() and p.is_file():
            target_file = p
    elif filename:
        p = (root_dir / filename).resolve()
        if p.exists() and p.is_file():
            target_file = p

    if target_file:
        try:
            target_file.unlink()
        except Exception as e:
            return 500, {"error": f"Error eliminando archivo: {e}"}

    recents = config.get("recent_conversions", [])
    recents = [
        r for r in recents if r.get("filename") != filename and r.get("file_path") != file_path_str
    ]
    config["recent_conversions"] = recents
    save_config_fn(config)

    try:
        if filename:
            remove_from_index_cache(root_dir, filename)
        elif file_path_str:
            remove_from_index_cache(root_dir, Path(file_path_str).name)
    except Exception:
        pass

    try:
        generate_index_html(root_dir)
        rem = [
            f
            for f in root_dir.glob("*.html")
            if f.name.lower() not in ("index.html", "latest.html")
        ]
        if rem:
            rem.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            newest = rem[0]
            newest_title = extract_title_from_html(newest)
            generate_latest_redirect(root_dir, newest, newest_title)
        else:
            latest_p = root_dir / "latest.html"
            if latest_p.exists():
                latest_p.unlink()
    except Exception as e:
        print(f"Aviso actualizando biblioteca tras eliminación: {e}")

    return 200, {
        "success": True,
        "filename": filename,
        "recent_conversions": config["recent_conversions"],
    }
