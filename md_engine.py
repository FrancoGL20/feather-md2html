#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML Engine — Apple Design System
Compilación de alto rendimiento (<25ms) sin dependencias externas.
Genera páginas HTML autónomas, barra de navegación cruzada, catálogo index.html y latest.html.
"""

import os
import sys
import re
import html
import unicodedata
from pathlib import Path
from datetime import datetime

# SVG Icons
ICON_DOC = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>"""
ICON_FOLDER = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>"""
ICON_BOLT = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>"""
ICON_COPY = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>"""
ICON_SEARCH = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>"""

ALERT_ICONS = {
    'note': """<svg viewBox="0 0 16 16" fill="currentColor"><path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75zM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>""",
    'tip': """<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.677.933.24.437.375.952.375 1.51h3.5c0-.558.135-1.073.375-1.51.207-.377.454-.669.677-.933l.214-.253c.56-.679.984-1.32.984-2.304 0-2.06-1.637-3.75-4-3.75zM6 11.75a.75.75 0 0 1 .75-.75h2.5a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1-.75-.75zm.75 2a.75.75 0 0 0 0 1.5h1.5a.75.75 0 0 0 0-1.5h-1.5z"/></svg>""",
    'important': """<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm7.25-3.25a.75.75 0 0 1 1.5 0v3.5a.75.75 0 0 1-1.5 0v-3.5zm.75 6.25a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>""",
    'warning': """<svg viewBox="0 0 16 16" fill="currentColor"><path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575L6.457 1.047zM8 5a.75.75 0 0 0-.75.75v3.5a.75.75 0 0 0 1.5 0v-3.5A.75.75 0 0 0 8 5zm0 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/></svg>""",
    'caution': """<svg viewBox="0 0 16 16" fill="currentColor"><path d="M4.47.04C4.267.014 4.06 0 3.85 0H1.75C.784 0 0 .784 0 1.75v2.1c0 .21.014.417.04.62l1.52 7.6c.14.7.75 1.2 1.46 1.2h9.96c.71 0 1.32-.5 1.46-1.2l1.52-7.6c.026-.203.04-.41.04-.62V1.75C16 .784 15.216 0 14.25 0h-2.1c-.21 0-.417.014-.62.04L8 1.48 4.47.04zM8 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 5zm0 7a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>"""
}

COMMON_STYLES = """
:root {
  --canvas-bg: #000000;
  --card-bg: #161617;
  --card-alt-bg: rgba(255, 255, 255, 0.04);
  --border-color: rgba(255, 255, 255, 0.1);
  --border-subtle: rgba(255, 255, 255, 0.05);
  --text-main: #f5f5f7;
  --text-muted: #a1a1a6;
  --text-faint: #6e6e73;
  --primary: #2997ff;
  --primary-hover: #47a7ff;
  --primary-surface: rgba(41, 151, 255, 0.12);
  --code-block-bg: #0d0d0e;
  --code-block-header: #19191b;
  --code-block-text: #f5f5f7;
  --code-inline-bg: rgba(255, 255, 255, 0.08);
  --code-inline-text: #f5f5f7;
  --table-stripe: rgba(255, 255, 255, 0.02);
  --table-hover: rgba(41, 151, 255, 0.06);
  --accent-badge-bg: rgba(41, 151, 255, 0.15);
  --accent-badge-text: #70baff;
  --success-badge-bg: rgba(48, 209, 88, 0.16);
  --success-badge-text: #30d158;
  --warning-badge-bg: rgba(255, 159, 10, 0.16);
  --warning-badge-text: #ff9f0a;
  --danger-badge-bg: rgba(255, 69, 58, 0.16);
  --danger-badge-text: #ff453a;
  --shadow-card: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.08);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.5);
  --shadow-float: 0 20px 50px rgba(0, 0, 0, 0.8);
  --glass-bg: rgba(22, 22, 23, 0.82);
  --glass-border: rgba(255, 255, 255, 0.12);
  --spring-curve: cubic-bezier(0.16, 1, 0.3, 1);
}

html.light {
  --canvas-bg: #f5f5f7;
  --card-bg: #ffffff;
  --card-alt-bg: rgba(0, 0, 0, 0.025);
  --border-color: rgba(0, 0, 0, 0.08);
  --border-subtle: rgba(0, 0, 0, 0.04);
  --text-main: #1d1d1f;
  --text-muted: #86868b;
  --text-faint: #a1a1a6;
  --primary: #0071e3;
  --primary-hover: #0077ed;
  --primary-surface: rgba(0, 113, 227, 0.07);
  --code-block-bg: #1d1d1f;
  --code-block-header: #28282b;
  --code-block-text: #f5f5f7;
  --code-inline-bg: rgba(0, 0, 0, 0.045);
  --code-inline-text: #1d1d1f;
  --table-stripe: rgba(0, 0, 0, 0.015);
  --table-hover: rgba(0, 113, 227, 0.04);
  --accent-badge-bg: rgba(0, 113, 227, 0.08);
  --accent-badge-text: #0071e3;
  --success-badge-bg: rgba(52, 199, 89, 0.12);
  --success-badge-text: #248a3d;
  --warning-badge-bg: rgba(255, 149, 0, 0.12);
  --warning-badge-text: #b25000;
  --danger-badge-bg: rgba(255, 59, 48, 0.12);
  --danger-badge-text: #d70015;
  --shadow-card: 0 4px 16px rgba(0, 0, 0, 0.03), 0 20px 44px -10px rgba(0, 0, 0, 0.06);
  --glass-bg: rgba(255, 255, 255, 0.82);
  --glass-border: rgba(255, 255, 255, 0.6);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  background-color: var(--canvas-bg);
  color: var(--text-main);
  line-height: 1.62;
  letter-spacing: -0.006em;
  padding: 1.5rem 1rem 4rem 1rem;
  transition: background-color 200ms ease, color 200ms ease;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  background-color: var(--card-bg);
  border-radius: 20px;
  box-shadow: var(--shadow-card);
  padding: 2.2rem 2.8rem;
  position: relative;
  border: 1px solid var(--border-color);
}

/* Apple Top Navigation Bar (Cross-Document) */
.top-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.85rem;
  margin-bottom: 2rem;
  background-color: var(--card-alt-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 9999px;
  border: 1px solid var(--border-color);
}

.nav-links-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nav-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.42rem 0.85rem;
  border-radius: 9999px;
  font-size: 0.82rem;
  font-weight: 550;
  text-decoration: none;
  color: var(--text-main);
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  transition: all 120ms var(--spring-curve);
  user-select: none;
  cursor: pointer;
}

.nav-pill-btn:hover {
  background-color: var(--primary-surface);
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-1px);
}

.nav-pill-btn:active {
  transform: scale(0.96);
}

.theme-toggle-btn {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  border-radius: 9999px;
  padding: 0.42rem 0.85rem;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  transition: all 120ms var(--spring-curve);
}

.theme-toggle-btn:hover {
  background-color: var(--card-alt-bg);
  transform: translateY(-1px);
}

.theme-toggle-btn:active {
  transform: scale(0.96);
}

.sun-icon { display: none; width: 14px; height: 14px; }
.moon-icon { display: inline-block; width: 14px; height: 14px; }
html.light .sun-icon { display: inline-block; }
html.light .moon-icon { display: none; }

/* Markdown Core Elements */
h1 {
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.15;
  margin-bottom: 0.5rem;
}

h2 {
  font-size: 1.55rem;
  font-weight: 650;
  letter-spacing: -0.025em;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--border-subtle);
}

h3 {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

p { margin-bottom: 1rem; }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Code Blocks */
.code-block {
  margin: 1.25rem 0 1.5rem 0;
  border-radius: 12px;
  overflow: hidden;
  background-color: var(--code-block-bg);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.code-header {
  background-color: var(--code-block-header);
  padding: 0.4rem 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.72rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #a1a1a6;
  text-transform: uppercase;
}

.copy-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f5f5f7;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.72rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 120ms ease;
}

.copy-btn:active { transform: scale(0.95); }
.copy-btn.copied { background: rgba(52, 199, 89, 0.2); border-color: #32d74b; color: #32d74b; }

pre {
  padding: 1rem;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.88rem;
  line-height: 1.55;
  color: var(--code-block-text);
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.88em;
  background-color: var(--code-inline-bg);
  color: var(--code-inline-text);
  padding: 0.15em 0.35em;
  border-radius: 6px;
}

/* Syntax Highlighting */
.tok-kw { color: #ff7b72; font-weight: 600; }
.tok-diff-add { color: #7ee787; background: rgba(46, 160, 67, 0.15); display: block; }
.tok-diff-del { color: #ffa198; background: rgba(218, 54, 51, 0.15); display: block; }

/* Tables */
.table-container {
  overflow-x: auto;
  margin: 1.25rem 0;
  border: 1px solid var(--border-color);
  border-radius: 12px;
}
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td { padding: 0.65rem 0.85rem; border-bottom: 1px solid var(--border-subtle); text-align: left; }
th { background-color: var(--card-alt-bg); font-weight: 600; }
tr:last-child td { border-bottom: none; }
tr:nth-child(even) td { background-color: var(--table-stripe); }
tr:hover td { background-color: var(--table-hover); }

/* Lists & Nested Hierarchies (Apple Human Interface Guidelines) */
ul, ol {
  margin-top: 0.5rem;
  margin-bottom: 0.95rem;
  padding-left: 1.7rem;
}

ul {
  list-style-type: disc;
}

ol {
  list-style-type: decimal;
}

li {
  margin-bottom: 0.35rem;
  line-height: 1.62;
}

/* Sublistas anidadas con sangría progresiva a la derecha y marcadores jerárquicos */
ul ul, ol ul {
  list-style-type: circle;
  margin-top: 0.35rem;
  margin-bottom: 0.35rem;
  padding-left: 1.5rem;
}

ul ul ul, ol ul ul, ul ol ul, ol ol ul {
  list-style-type: square;
  padding-left: 1.5rem;
}

ol ol, ul ol {
  list-style-type: lower-alpha;
  margin-top: 0.35rem;
  margin-bottom: 0.35rem;
  padding-left: 1.5rem;
}

ol ol ol, ul ol ol, ol ul ol, ul ul ol {
  list-style-type: lower-roman;
  padding-left: 1.5rem;
}

/* Task list (Apple Reminders style) */
ul.task-list {
  list-style: none;
  padding-left: 0;
  margin-top: 0.5rem;
  margin-bottom: 0.95rem;
}

li.task-item {
  display: block;
  margin-bottom: 0.4rem;
  line-height: 1.62;
}

li.task-item > div.task-line {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
}

li.task-item input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--border-color);
  border-radius: 5px;
  outline: none;
  cursor: default;
  background: var(--card-bg);
  transform: translateY(2px);
  flex-shrink: 0;
  transition: all 120ms ease;
}

li.task-item input[type="checkbox"]:checked {
  background: var(--primary);
  border-color: var(--primary);
}

li.task-item input[type="checkbox"]:checked::before {
  content: "✓";
  display: block;
  color: #fff;
  font-size: 11px;
  text-align: center;
  line-height: 14px;
}

li.task-item.checked > div.task-line > span,
li.task-item.checked > span {
  text-decoration: line-through;
  color: var(--text-faint);
}

/* Sublistas anidadas dentro de task items */
li.task-item > ul,
li.task-item > ol {
  padding-left: 1.7rem;
  margin-top: 0.35rem;
  margin-bottom: 0.35rem;
}

/* Horizontal Rules */
hr {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 2rem 0;
}

/* Alerts / Callouts */
.alert {
  border: 1px solid var(--border-color);
  border-left-width: 4px;
  border-radius: 12px;
  padding: 0.9rem 1.2rem;
  margin: 1.2rem 0;
  background-color: var(--card-alt-bg);
}
.alert-note { border-left-color: var(--primary); }
.alert-tip { border-left-color: #30d158; }
.alert-important { border-left-color: #a25ddc; }
.alert-warning { border-left-color: #ff9f0a; }
.alert-caution { border-left-color: #ff453a; }
.alert-header { font-weight: 650; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.45rem; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
.alert-header svg { width: 15px; height: 15px; }

/* Status Badges */
.badge { display: inline-block; padding: 0.15rem 0.5rem; font-size: 0.72rem; font-weight: 650; border-radius: 9999px; text-transform: uppercase; }
.badge-success { background: var(--success-badge-bg); color: var(--success-badge-text); }
.badge-danger { background: var(--danger-badge-bg); color: var(--danger-badge-text); }
.badge-warning { background: var(--warning-badge-bg); color: var(--warning-badge-text); }
.badge-info { background: var(--accent-badge-bg); color: var(--accent-badge-text); }

/* Table of Contents */
.toc-box {
  background-color: var(--card-alt-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 0.9rem 1.25rem;
  margin: 1.2rem 0 1.8rem 0;
}
.toc-box summary { font-weight: 650; cursor: pointer; user-select: none; }
.toc-nav { margin-top: 0.7rem; }
.toc-nav ul { list-style: none; padding-left: 0.5rem; }
.toc-nav li { margin-bottom: 0.35rem; font-size: 0.9rem; }

.header-meta {
  display: flex; gap: 1rem; color: var(--text-muted); font-size: 0.8rem;
  margin-top: 0.4rem; margin-bottom: 1.5rem; flex-wrap: wrap;
}

footer {
  margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--border-subtle);
  font-size: 0.78rem; color: var(--text-faint); display: flex; justify-content: space-between;
}

@media (max-width: 768px) {
  .container { padding: 1.5rem 1.2rem; }
  h1 { font-size: 1.8rem; }
}
"""

HTML_DOC_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232997ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'></path><polyline points='14 2 14 8 20 8'></polyline></svg>">
  <style>
{styles}
  </style>
</head>
<body>
  <div class="container">
    <!-- Apple Top Navigation Bar (Navegación Cruzada) -->
    <nav class="top-nav-bar" aria-label="Navegación de biblioteca">
      <div class="nav-links-group">
        <a href="./index.html" class="nav-pill-btn" title="Ir al catálogo de todos los archivos generados">
          {icon_folder}
          <span>Índice de Documentos</span>
        </a>
        <a href="./latest.html" class="nav-pill-btn" title="Ir a la página más nueva creada">
          {icon_bolt}
          <span>Más Reciente</span>
        </a>
      </div>
      <button class="theme-toggle-btn" id="theme-btn" onclick="toggleTheme()" title="Alternar tema claro/oscuro">
        <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg class="moon-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
        <span>Tema</span>
      </button>
    </nav>

    <header>
      <h1>{header_title} {header_badge}</h1>
      {header_subtitle}
      <div class="header-meta">
        <span>⏱️ {reading_time}</span>
        <span>📝 {word_count} palabras</span>
        <span>📅 Generado el {generated_date}</span>
      </div>
    </header>

    <main>
{toc_content}
{body_content}
    </main>

    <footer>
      <span>Biblioteca Markdown HTML</span>
      <span>{footer_date}</span>
    </footer>
  </div>

  <script>
    function initTheme() {{
      const saved = localStorage.getItem('apple-md-theme');
      if (saved === 'light') {{
        document.documentElement.classList.add('light');
      }} else if (saved === 'dark') {{
        document.documentElement.classList.remove('light');
      }}
    }}
    function toggleTheme() {{
      const isLight = document.documentElement.classList.contains('light');
      if (isLight) {{
        document.documentElement.classList.remove('light');
        localStorage.setItem('apple-md-theme', 'dark');
      }} else {{
        document.documentElement.classList.add('light');
        localStorage.setItem('apple-md-theme', 'light');
      }}
    }}
    initTheme();

    function copyCode(btn) {{
      const code = btn.closest('.code-block').querySelector('pre code').innerText;
      navigator.clipboard.writeText(code).then(() => {{
        const orig = btn.innerHTML;
        btn.classList.add('copied');
        btn.innerHTML = '✓ Copiado';
        setTimeout(() => {{
          btn.innerHTML = orig;
          btn.classList.remove('copied');
        }}, 2000);
      }});
    }}
  </script>
</body>
</html>
"""

def escape(text: str) -> str:
    return html.escape(text, quote=False)

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    slug = re.sub(r'[-\s]+', '-', text)
    return slug or "documento"

def format_status_badges(text: str) -> str:
    patterns = [
        (r'\[(PASS|PASSED|APROBADO|OK|EXITOSO)\]', r'<span class="badge badge-success">\1</span>'),
        (r'\[(FAIL|FAILED|FALLO|ERROR|REPROBADO)\]', r'<span class="badge badge-danger">\1</span>'),
        (r'\[(WARN|WARNING|ADVERTENCIA|PENDIENTE|PENDING)\]', r'<span class="badge badge-warning">\1</span>'),
        (r'\[(INFO|NOTA|RECOMENDADO|RECOMMENDED)\]', r'<span class="badge badge-info">\1</span>'),
    ]
    for pat, rep in patterns:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text

def inline_formatting(text: str) -> str:
    code_tokens = []
    def code_repl(m):
        code_tokens.append(f"<code>{escape(m.group(1))}</code>")
        return f"\x00INLINECODE{len(code_tokens)-1}\x00"
    text = re.sub(r'`([^`]+)`', code_repl, text)

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width: 100%; border-radius: 12px; margin: 0.6rem 0; box-shadow: var(--shadow-sm);">', text)
    def link_repl(m):
        link_text = m.group(1)
        href = m.group(2).strip()
        if href.startswith('#'):
            slug_href = "#" + slugify(href[1:])
            return f'<a href="{slug_href}">{link_text}</a>'
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{link_text}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!_)_(?!_)(.*?)(?<!_)_(?!_)', r'<em>\1</em>', text)
    text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)
    text = format_status_badges(text)

    for i, tok in enumerate(code_tokens):
        text = text.replace(f"\x00INLINECODE{i}\x00", tok)
    return text

def highlight_code_block(code_raw: str, lang: str) -> str:
    esc = escape(code_raw)
    lang_lower = (lang or '').lower().strip()
    if lang_lower == 'diff':
        lines = []
        for line in esc.splitlines():
            if line.startswith('+'):
                lines.append(f'<span class="tok-diff-add">{line}</span>')
            elif line.startswith('-'):
                lines.append(f'<span class="tok-diff-del">{line}</span>')
            else:
                lines.append(line)
        return "\n".join(lines)
    keywords = {
        'python': r'\b(def|class|return|import|from|as|if|elif|else|for|while|try|except|finally|raise|with|pass|lambda|yield|True|False|None|and|or|not|is|in)\b',
        'javascript': r'\b(function|const|let|var|return|if|else|for|while|try|catch|finally|throw|class|new|import|from|export|default|true|false|null|undefined|async|await)\b',
        'json': r'\b(true|false|null)\b',
        'powershell': r'\b(function|param|if|else|elseif|foreach|while|try|catch|finally|return|throw|switch)\b'
    }
    kw_regex = keywords.get(lang_lower)
    if kw_regex:
        esc = re.sub(kw_regex, r'<span class="tok-kw">\1</span>', esc)
    return esc

def clean_markdown_inline(text: str) -> str:
    """Elimina formato markdown básico para obtener texto plano limpio para títulos."""
    if not text:
        return ""
    # Quitar etiquetas HTML
    text = re.sub(r'<[^>]+>', '', text)
    # Quitar código en línea
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Quitar enlaces [texto](url) -> texto
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Quitar imágenes ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Quitar negritas y cursivas
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_(?!_)(.*?)(?<!_)_(?!_)', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    # Quitar badges [PASS], [FAIL], etc.
    text = re.sub(r'\[(PASS|PASSED|APROBADO|OK|EXITOSO|FAIL|FAILED|FALLO|ERROR|REPROBADO|WARN|WARNING|ADVERTENCIA|PENDIENTE|PENDING|INFO|NOTA|RECOMENDADO)\]', '', text, flags=re.IGNORECASE)
    # Quitar símbolos o prefijos sobrantes al inicio/final como #, -, *, :, espacios
    text = re.sub(r'^[#\s\-*:]+', '', text)
    return text.strip()

def format_stem_as_title(stem: str) -> str:
    """Convierte un nombre de archivo en un título legible."""
    stem = re.sub(r'_\d{8}_\d{6}$', '', stem)
    stem = re.sub(r'_\d{8}$', '', stem)
    title = re.sub(r'[-_]+', ' ', stem).strip()
    words = [w.capitalize() if not w.isupper() else w for w in title.split()]
    return " ".join(words)

def detect_smart_title(lines: list, custom_title: str = None, input_file_path: str = None, frontmatter: dict = None) -> tuple:
    """
    Detecta el título más representativo y limpio para el documento.
    Retorna: (title, title_source, title_line_index)
    title_source: 'custom', 'frontmatter', 'h1', 'setext_h1', 'h2', 'setext_h2', 'h3', 'file_stem', 'bold_line', 'first_line', 'fallback'
    """
    # 1. Título explícito ingresado por el usuario
    if custom_title and custom_title.strip():
        return clean_markdown_inline(custom_title.strip()), 'custom', -1

    # 2. YAML Frontmatter
    if frontmatter:
        for k in ('title', 'name', 'subject', 'topic', 'titulo', 'heading'):
            val = frontmatter.get(k)
            if val and str(val).strip():
                return clean_markdown_inline(str(val).strip()), 'frontmatter', -1

    n = len(lines)

    # 3. Encabezados H1 explícitos (# o Setext ===)
    for idx, l in enumerate(lines):
        st = l.strip()
        m_h1 = re.match(r'^#\s+(.+)$', st)
        if m_h1:
            cl = clean_markdown_inline(m_h1.group(1))
            if cl:
                return cl, 'h1', idx
        if idx + 1 < n and st and not st.startswith(('#', '```', '>', '|', '- ', '* ', '+ ')):
            if re.match(r'^[=]{3,}\s*$', lines[idx + 1].strip()):
                cl = clean_markdown_inline(st)
                if cl:
                    return cl, 'setext_h1', idx

    # 4. Encabezados H2 (## o Setext ---) o H3 (###) si no hay ningún H1
    for idx, l in enumerate(lines):
        st = l.strip()
        m_h2 = re.match(r'^##\s+(.+)$', st)
        if m_h2:
            cl = clean_markdown_inline(m_h2.group(1))
            if cl:
                return cl, 'h2', idx
        if idx + 1 < n and st and not st.startswith(('#', '```', '>', '|', '- ', '* ', '+ ', '---')):
            if re.match(r'^[-]{3,}\s*$', lines[idx + 1].strip()):
                cl = clean_markdown_inline(st)
                if cl:
                    return cl, 'setext_h2', idx

    for idx, l in enumerate(lines):
        st = l.strip()
        m_h3 = re.match(r'^###\s+(.+)$', st)
        if m_h3:
            cl = clean_markdown_inline(m_h3.group(1))
            if cl:
                return cl, 'h3', idx

    # 5. Nombre de archivo físico de entrada (si se subió archivo y el stem no es genérico)
    if input_file_path:
        stem = Path(input_file_path).stem
        if stem.lower() not in ('temp', 'input', 'a', 'b', 'test', 'tmp', 'untitled', 'document', 'documento'):
            candidate = format_stem_as_title(stem)
            if candidate:
                return candidate, 'file_stem', -1

    # 6. Primera línea en negrita destacada (ej. **Reporte de Cobertura**)
    for idx, l in enumerate(lines[:15]):
        st = l.strip()
        if not st or st.startswith(('#', '```', '>', '|', '---', '===', '***')):
            continue
        m_bold = re.match(r'^\s*(\*\*|__)(.*?)\1\s*$', st)
        if m_bold:
            cl = clean_markdown_inline(m_bold.group(2))
            if len(cl) >= 3:
                return cl, 'bold_line', idx

    # 7. Primera línea significativa de texto
    for idx, l in enumerate(lines[:20]):
        st = l.strip()
        if not st or st.startswith(('#', '```', '>', '|', '---', '===', '***', '<!--', '<')):
            continue
        cl = clean_markdown_inline(st)
        if len(cl) >= 4:
            if len(cl) > 70:
                truncated = cl[:70].rsplit(' ', 1)[0]
                cl = f"{truncated}..."
            return cl, 'first_line', idx

    # 8. Fallback contextual con fecha/hora en lugar de genérico 'Documento'
    now_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    return f"Documento Markdown ({now_str})", 'fallback', -1

class ListNode:
    def __init__(self, list_type, start_num=1):
        self.list_type = list_type  # 'ul', 'ol', 'task'
        self.start_num = start_num
        self.items = []

class ItemNode:
    def __init__(self, text, is_task=False, checked=False):
        self.text = text
        self.is_task = is_task
        self.checked = checked
        self.children = []

def is_list_marker(line: str) -> bool:
    if not line:
        return False
    clean = line.expandtabs(4)
    stripped = clean.strip()
    if not stripped:
        return False
    # Evitar confusión con líneas horizontales (---, ***, ___)
    if re.match(r'^(?:[-*_]\s*){3,}$', stripped):
        return False
    # Task item: - [ ] o * [ ] o + [ ]
    if re.match(r'^\s*[-*+]\s+\[([ xX])\](?:\s+.*)?$', clean):
        return True
    # Unordered item: - , * , +
    if re.match(r'^\s*[-*+]\s+(?:.*)?$', clean):
        return True
    # Ordered item: 1. , 1)
    if re.match(r'^\s*\d+[\.\)]\s+(?:.*)?$', clean):
        return True
    return False

def render_list_node(node: ListNode) -> str:
    if node.list_type == 'task':
        tag = 'ul class="task-list"'
        close_tag = 'ul'
    elif node.list_type == 'ol':
        if node.start_num != 1:
            tag = f'ol start="{node.start_num}"'
        else:
            tag = 'ol'
        close_tag = 'ol'
    else:
        tag = 'ul'
        close_tag = 'ul'
    
    out = [f'<{tag}>']
    for it in node.items:
        out.append(render_item_node(it))
    out.append(f'</{close_tag}>')
    return "\n".join(out)

def render_item_node(item: ItemNode) -> str:
    formatted_text = inline_formatting(item.text)
    if item.is_task:
        chk_attr = ' checked' if item.checked else ''
        cls = 'task-item checked' if item.checked else 'task-item'
        prefix = f'<li class="{cls}"><div class="task-line"><input type="checkbox"{chk_attr} disabled> <span>{formatted_text}</span></div>'
    else:
        prefix = f'<li>{formatted_text}'
    
    if item.children:
        child_htmls = [render_list_node(ch) for ch in item.children]
        return f'{prefix}\n' + "\n".join(child_htmls) + '\n</li>'
    else:
        return f'{prefix}</li>'

def parse_list_items(lines, start_idx):
    """
    Parsea un bloque continuo de lista a partir de start_idx.
    Retorna (raw_items, next_idx).
    """
    raw_items = []
    i = start_idx
    n = len(lines)
    
    while i < n:
        line = lines[i]
        clean = line.expandtabs(4)
        stripped = clean.strip()
        
        # Línea en blanco
        if not stripped:
            peek = i + 1
            while peek < n and not lines[peek].strip():
                peek += 1
            if peek < n and is_list_marker(lines[peek]):
                i += 1
                continue
            else:
                break
                
        # Marcador de lista
        if is_list_marker(clean):
            m_task = re.match(r'^(\s*)([-*+])\s+\[([ xX])\](?:\s+(.*)|\s*)$', clean)
            if m_task:
                raw_items.append({
                    'indent': len(m_task.group(1)),
                    'list_type': 'task',
                    'is_task': True,
                    'checked': m_task.group(3).lower() == 'x',
                    'text': m_task.group(4) or '',
                    'start_num': 1
                })
                i += 1
                continue
            m_ul = re.match(r'^(\s*)([-*+])\s+(.*)$', clean)
            if m_ul:
                raw_items.append({
                    'indent': len(m_ul.group(1)),
                    'list_type': 'ul',
                    'is_task': False,
                    'checked': False,
                    'text': m_ul.group(3),
                    'start_num': 1
                })
                i += 1
                continue
            m_ol = re.match(r'^(\s*)(\d+)[\.\)]\s+(.*)$', clean)
            if m_ol:
                raw_items.append({
                    'indent': len(m_ol.group(1)),
                    'list_type': 'ol',
                    'is_task': False,
                    'checked': False,
                    'text': m_ol.group(3),
                    'start_num': int(m_ol.group(2))
                })
                i += 1
                continue
                
        # Línea de continuación (sangrada y que no sea inicio de bloque principal)
        if raw_items and stripped and not stripped.startswith(('#', '```', '>', '|', '---', '===', '***')):
            indent = len(clean) - len(clean.lstrip(' '))
            if indent >= 2:
                raw_items[-1]['text'] += " " + stripped
                i += 1
                continue
                
        # Fin de la lista
        break
        
    return raw_items, i

def build_tree(raw_items):
    """
    Construye el árbol jerárquico anidado de ListNode e ItemNode a partir de los items parseados.
    """
    if not raw_items:
        return []
    
    root_lists = []
    # stack: list of {'indent': int, 'list_node': ListNode, 'last_item': ItemNode}
    stack = []
    
    for it_data in raw_items:
        indent = it_data['indent']
        item_node = ItemNode(it_data['text'], it_data['is_task'], it_data['checked'])
        
        if not stack:
            ln = ListNode(it_data['list_type'], it_data['start_num'])
            ln.items.append(item_node)
            root_lists.append(ln)
            stack.append({'indent': indent, 'list_node': ln, 'last_item': item_node})
            continue
            
        # Desapilar si la sangría actual es menor que la del nivel superior
        while len(stack) > 1 and indent < stack[-1]['indent']:
            if indent > stack[-2]['indent']:
                # Tolerancia: sangría ligeramente menor pero aún hija del ancestro
                break
            stack.pop()
            
        top = stack[-1]
        
        if indent > top['indent']:
            # Nivel anidado más profundo: hijo del último item del contenedor padre
            ln = ListNode(it_data['list_type'], it_data['start_num'])
            ln.items.append(item_node)
            top['last_item'].children.append(ln)
            stack.append({'indent': indent, 'list_node': ln, 'last_item': item_node})
        else:
            # Mismo nivel de sangría (hermano)
            if it_data['list_type'] == top['list_node'].list_type:
                top['list_node'].items.append(item_node)
                top['last_item'] = item_node
            else:
                ln = ListNode(it_data['list_type'], it_data['start_num'])
                ln.items.append(item_node)
                if len(stack) > 1:
                    parent_item = stack[-2]['last_item']
                    parent_item.children.append(ln)
                else:
                    root_lists.append(ln)
                stack[-1] = {'indent': indent, 'list_node': ln, 'last_item': item_node}
                
    return root_lists

def parse_markdown(md_text: str, custom_title: str = None, input_file_path: str = None):
    md_text = md_text.lstrip('\ufeff')
    lines = md_text.splitlines()

    frontmatter = {}
    idx = 0
    if len(lines) > 0 and lines[0].strip() == '---':
        idx = 1
        fm_lines = []
        while idx < len(lines) and lines[idx].strip() != '---':
            fm_lines.append(lines[idx])
            idx += 1
        if idx < len(lines):
            idx += 1
            for fml in fm_lines:
                if ':' in fml:
                    k, v = fml.split(':', 1)
                    frontmatter[k.strip().lower()] = v.strip().strip('"').strip("'")
    
    body_lines = lines[idx:]

    # Detección inteligente del título
    smart_title, title_src, title_line_idx = detect_smart_title(
        lines=body_lines,
        custom_title=custom_title,
        input_file_path=input_file_path,
        frontmatter=frontmatter
    )

    html_blocks = []
    toc_items = []
    title_line_consumed = False

    i = 0
    n = len(body_lines)
    while i < n:
        line = body_lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        # Si esta línea fue la elegida como título principal del documento,
        # la consumimos aquí para no duplicar el encabezado justo debajo del título principal
        if not title_line_consumed and i == title_line_idx:
            title_line_consumed = True
            if title_src in ('setext_h1', 'setext_h2'):
                i += 2
            else:
                i += 1
            continue

        # Bloques Setext Headings no consumidos como título
        if i + 1 < n and stripped and not stripped.startswith(('#', '```', '>', '|', '- ', '* ', '+ ', '---', '===')):
            next_line = body_lines[i + 1].strip()
            if re.match(r'^[=]{3,}\s*$', next_line):
                slug = slugify(stripped)
                heading_content = inline_formatting(stripped)
                html_blocks.append(f'<h1 id="{slug}">{heading_content}</h1>')
                i += 2
                continue
            elif re.match(r'^[-]{3,}\s*$', next_line) and not stripped.startswith('-'):
                slug = slugify(stripped)
                toc_items.append((2, stripped, slug))
                heading_content = inline_formatting(stripped)
                html_blocks.append(f'<h2 id="{slug}">{heading_content}</h2>')
                i += 2
                continue

        # Code block
        if stripped.startswith('```'):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < n and not body_lines[i].strip().startswith('```'):
                code_lines.append(body_lines[i])
                i += 1
            if i < n:
                i += 1
            code_raw = "\n".join(code_lines)
            code_html = highlight_code_block(code_raw, lang)
            lang_label = escape(lang.upper() if lang else "CODE")
            html_blocks.append(
                f'<div class="code-block">\n'
                f'  <div class="code-header">\n'
                f'    <span>{lang_label}</span>\n'
                f'    <button class="copy-btn" onclick="copyCode(this)">{ICON_COPY}<span>Copiar</span></button>\n'
                f'  </div>\n'
                f'  <pre><code>{code_html}</code></pre>\n'
                f'</div>'
            )
            continue

        # Headings estándar con #
        heading_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_raw = heading_match.group(2).strip()
            slug = slugify(heading_raw)

            if level in (2, 3):
                toc_items.append((level, heading_raw, slug))

            heading_content = inline_formatting(heading_raw)
            html_blocks.append(f'<h{level} id="{slug}">{heading_content}</h{level}>')
            i += 1
            continue

        # Alerts [!NOTE], [!TIP], etc.
        alert_match = re.match(r'^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$', line, re.IGNORECASE)
        if alert_match:
            alert_type = alert_match.group(1).lower()
            alert_header_text = alert_match.group(2).strip() or alert_type.upper()
            alert_body_lines = []
            i += 1
            while i < n and (body_lines[i].startswith('>') or not body_lines[i].strip()):
                if body_lines[i].startswith('>'):
                    sub_line = re.sub(r'^>\s?', '', body_lines[i])
                    alert_body_lines.append(sub_line)
                i += 1
            alert_icon = ALERT_ICONS.get(alert_type, ALERT_ICONS['note'])
            alert_body_html = "<br>".join([inline_formatting(l) for l in alert_body_lines if l.strip()])
            html_blocks.append(
                f'<div class="alert alert-{alert_type}">\n'
                f'  <div class="alert-header">{alert_icon} <span>{alert_header_text}</span></div>\n'
                f'  <div>{alert_body_html}</div>\n'
                f'</div>'
            )
            continue

        # Standard Blockquote
        if line.startswith('>'):
            bq_lines = []
            while i < n and (body_lines[i].startswith('>') or not body_lines[i].strip()):
                if body_lines[i].startswith('>'):
                    bq_lines.append(re.sub(r'^>\s?', '', body_lines[i]))
                i += 1
            bq_content = "<br>".join([inline_formatting(l) for l in bq_lines if l.strip()])
            html_blocks.append(f'<blockquote><p>{bq_content}</p></blockquote>')
            continue

        # Tables
        if '|' in line and i + 1 < n and re.match(r'^\s*\|?\s*:?---', body_lines[i + 1]):
            table_lines = [line]
            i += 1
            while i < n and '|' in body_lines[i]:
                table_lines.append(body_lines[i])
                i += 1
            headers = [c.strip() for c in table_lines[0].strip().strip('|').split('|')]
            rows = []
            for r_line in table_lines[2:]:
                cells = [c.strip() for c in r_line.strip().strip('|').split('|')]
                rows.append(cells)
            th_html = "".join([f"<th>{inline_formatting(h)}</th>" for h in headers])
            tr_html = []
            for r in rows:
                tds = "".join([f"<td>{inline_formatting(c)}</td>" for c in r])
                tr_html.append(f"<tr>{tds}</tr>")
            html_blocks.append(
                f'<div class="table-container">\n'
                f'  <table>\n'
                f'    <thead><tr>{th_html}</tr></thead>\n'
                f'    <tbody>{"".join(tr_html)}</tbody>\n'
                f'  </table>\n'
                f'</div>'
            )
            continue

        # Horizontal Rule (---, ***, ___)
        if re.match(r'^(?:[-*_]\s*){3,}$', stripped):
            html_blocks.append('<hr>')
            i += 1
            continue

        # Lists (Ordered, Unordered, Task, Nested Hierarchies)
        if is_list_marker(line):
            raw_items, next_i = parse_list_items(body_lines, i)
            roots = build_tree(raw_items)
            for r in roots:
                html_blocks.append(render_list_node(r))
            i = next_i
            continue

        # Paragraph
        para_lines = []
        while (i < n and body_lines[i].strip() 
               and not body_lines[i].strip().startswith(('#', '```', '>', '|'))
               and not re.match(r'^(?:[-*_]\s*){3,}$', body_lines[i].strip())
               and not is_list_marker(body_lines[i])):
            para_lines.append(body_lines[i].strip())
            i += 1
        if para_lines:
            para_text = " ".join(para_lines)
            html_blocks.append(f'<p>{inline_formatting(para_text)}</p>')

    # Table of contents if 3+ items
    toc_html = ""
    if len(toc_items) >= 3:
        toc_li = []
        for lvl, text, slug in toc_items:
            pad = "&nbsp;&nbsp;" if lvl == 3 else ""
            toc_li.append(f'<li>{pad}<a href="#{slug}">{escape(text)}</a></li>')
        toc_html = (
            f'<details class="toc-box" open>\n'
            f'  <summary>📑 Índice de Contenidos</summary>\n'
            f'  <nav class="toc-nav"><ul>{"".join(toc_li)}</ul></nav>\n'
            f'</details>'
        )

    final_title = smart_title or "Documento"
    return {
        "title": final_title,
        "badge": "",
        "subtitle": "",
        "body": "\n".join(html_blocks),
        "toc": toc_html,
        "frontmatter": frontmatter
    }

def generate_index_html(root_dir: Path) -> Path:
    """
    Genera o actualiza el archivo index.html en el directorio raíz.
    Lista todos los documentos HTML generados ordenados de más nuevo a más viejo.
    """
    html_files = []
    for f in root_dir.glob("*.html"):
        if f.name.lower() in ("index.html", "latest.html"):
            continue
        try:
            stat = f.stat()
            mtime = stat.st_mtime
            size_kb = max(1, round(stat.st_size / 1024))
            # Extraer título del archivo si es posible
            doc_title = f.stem.replace("-", " ").replace("_", " ").capitalize()
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    head_chunk = fh.read(4000)
                    t_match = re.search(r'<title>(.*?)</title>', head_chunk, re.IGNORECASE)
                    if t_match and t_match.group(1).strip():
                        doc_title = t_match.group(1).strip()
            except Exception:
                pass

            dt = datetime.fromtimestamp(mtime)
            html_files.append({
                "path": f,
                "filename": f.name,
                "title": doc_title,
                "mtime": mtime,
                "date_str": dt.strftime("%d/%m/%Y, %I:%M %p"),
                "size_kb": size_kb
            })
        except Exception:
            continue

    # Ordenar de más nuevo a más viejo
    html_files.sort(key=lambda x: x["mtime"], reverse=True)

    items_html = []
    for doc in html_files:
        fn = escape(doc["filename"])
        ttl = escape(doc["title"])
        dt_s = escape(doc["date_str"])
        items_html.append(f"""
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
        """)

    cards_markup = "".join(items_html) if items_html else """
    <div class="empty-state">
      <div class="empty-state-icon">📂</div>
      <h3>No hay documentos generados todavía</h3>
      <p>Genera tu primer documento desde la aplicación de escritorio y aparecerá listado aquí automáticamente.</p>
    </div>
    """

    newest_link = f'./{html_files[0]["filename"]}' if html_files else './index.html'

    index_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Índice de Documentos HTML</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232997ff' stroke-width='2'><path d='M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z'></path></svg>">
  <style>
{COMMON_STYLES}

.index-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}}

.index-title-area h1 {{
  margin-bottom: 0.25rem;
}}

.index-subtitle {{
  color: var(--text-muted);
  font-size: 0.95rem;
}}

.search-box-wrap {{
  margin: 1.5rem 0 2rem 0;
  position: relative;
}}

.search-input {{
  width: 100%;
  padding: 0.85rem 1rem 0.85rem 2.8rem;
  background-color: var(--card-alt-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-main);
  font-size: 0.95rem;
  font-family: inherit;
  outline: none;
  transition: all 150ms var(--spring-curve);
}}

.search-input:focus {{
  border-color: var(--primary);
  background-color: var(--card-bg);
  box-shadow: 0 0 0 3px var(--primary-surface);
}}

.search-icon-inside {{
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}}

.docs-grid {{
  display: flex;
  flex-direction: column;
  gap: 1rem;
}}

.doc-card {{
  background-color: var(--card-alt-bg);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 1.25rem 1.45rem;
  transition: transform 120ms var(--spring-curve), border-color 120ms ease;
}}

.doc-card:hover {{
  border-color: var(--primary);
  transform: translateY(-1px);
}}

.doc-card-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}}

.doc-card-title-group {{
  display: flex;
  align-items: center;
  gap: 0.65rem;
}}

.doc-card-icon {{
  color: var(--primary);
  display: flex;
  align-items: center;
}}

.doc-card-title {{
  font-size: 1.15rem;
  font-weight: 650;
  margin: 0;
  border: none;
  padding: 0;
}}

.doc-card-title a {{
  color: var(--text-main);
  text-decoration: none;
}}

.doc-card-title a:hover {{
  color: var(--primary);
}}

.doc-card-date {{
  font-size: 0.8rem;
  color: var(--text-muted);
}}

.doc-card-meta {{
  display: flex;
  gap: 0.85rem;
  align-items: center;
  margin-bottom: 1rem;
}}

.doc-card-slug {{
  font-size: 0.78rem;
}}

.doc-card-size {{
  font-size: 0.78rem;
  color: var(--text-faint);
}}

.doc-card-actions {{
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}}

.doc-btn {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 550;
  text-decoration: none;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 120ms ease;
  user-select: none;
}}

.doc-btn:active {{
  transform: scale(0.96);
}}

.doc-btn-primary {{
  background-color: var(--primary);
  color: #ffffff;
}}

.doc-btn-primary:hover {{
  background-color: var(--primary-hover);
  text-decoration: none;
}}

.doc-btn-secondary {{
  background-color: var(--card-bg);
  border-color: var(--border-color);
  color: var(--text-main);
}}

.doc-btn-secondary:hover {{
  background-color: var(--card-alt-bg);
}}

.empty-state {{
  text-align: center;
  padding: 3.5rem 1rem;
  color: var(--text-muted);
}}
.empty-state-icon {{ font-size: 3rem; margin-bottom: 0.5rem; }}
  </style>
</head>
<body>
  <div class="container">
    <nav class="top-nav-bar" aria-label="Navegación">
      <div class="nav-links-group">
        <a href="{newest_link}" class="nav-pill-btn" title="Ir al documento más nuevo creado">
          {ICON_BOLT}
          <span>Documento Más Reciente</span>
        </a>
      </div>
      <button class="theme-toggle-btn" id="theme-btn" onclick="toggleTheme()" title="Alternar tema">
        <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg class="moon-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
        <span>Tema</span>
      </button>
    </nav>

    <header class="index-header">
      <div class="index-title-area">
        <h1>Biblioteca de Documentos</h1>
        <p class="index-subtitle">Catálogo cronológico ordenado del más nuevo al más viejo ({len(html_files)} documentos)</p>
      </div>
    </header>

    <div class="search-box-wrap">
      <span class="search-icon-inside">{ICON_SEARCH}</span>
      <input type="text" id="searchInput" class="search-input" placeholder="Buscar por título o nombre de archivo..." oninput="filterDocuments()">
    </div>

    <div class="docs-grid" id="docsGrid">
      {cards_markup}
    </div>

    <footer>
      <span>Biblioteca Markdown HTML</span>
      <span>Directorio Raíz: {escape(str(root_dir))}</span>
    </footer>
  </div>

  <script>
    function initTheme() {{
      const saved = localStorage.getItem('apple-md-theme');
      if (saved === 'light') {{
        document.documentElement.classList.add('light');
      }} else if (saved === 'dark') {{
        document.documentElement.classList.remove('light');
      }}
    }}
    function toggleTheme() {{
      const isLight = document.documentElement.classList.contains('light');
      if (isLight) {{
        document.documentElement.classList.remove('light');
        localStorage.setItem('apple-md-theme', 'dark');
      }} else {{
        document.documentElement.classList.add('light');
        localStorage.setItem('apple-md-theme', 'light');
      }}
    }}
    initTheme();

    function filterDocuments() {{
      const q = document.getElementById('searchInput').value.toLowerCase().trim();
      const cards = document.querySelectorAll('.doc-card');
      cards.forEach(card => {{
        const title = card.getAttribute('data-title') || '';
        const file = card.getAttribute('data-file') || '';
        if (!q || title.includes(q) || file.includes(q)) {{
          card.style.display = 'block';
        }} else {{
          card.style.display = 'none';
        }}
      }});
    }}

    function copyDocLink(filename, btn) {{
      const fullUrl = new URL(filename, window.location.href).href;
      navigator.clipboard.writeText(fullUrl).then(() => {{
        const label = btn.querySelector('span');
        const orig = label ? label.textContent : '';
        if (label) label.textContent = '✓ Copiado';
        setTimeout(() => {{
          if (label) label.textContent = orig;
        }}, 2000);
      }});
    }}
  </script>
</body>
</html>
"""
    index_file = root_dir / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)
    return index_file

def generate_latest_redirect(root_dir: Path, newest_file: Path, doc_title: str) -> Path:
    """
    Genera latest.html que redirige inmediatamente al archivo más reciente.
    """
    rel_name = newest_file.name
    latest_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=./{rel_name}">
  <title>Redirigiendo al más reciente...</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232997ff' stroke-width='2'><polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'></polygon></svg>">
  <style>
{COMMON_STYLES}
  </style>
</head>
<body>
  <div class="container" style="text-align: center; margin-top: 4rem;">
    <h2>Redirigiendo al documento más reciente...</h2>
    <p style="color: var(--text-muted); margin: 1rem 0 1.5rem 0;">{escape(doc_title)} (<code>{rel_name}</code>)</p>
    <a href="./{rel_name}" class="doc-btn doc-btn-primary" style="display: inline-block;">Abrir ahora</a>
    <div style="margin-top: 2rem;">
      <a href="./index.html" style="color: var(--text-faint); font-size: 0.85rem;">Ir al Índice de Documentos</a>
    </div>
  </div>
</body>
</html>
"""
    latest_file = root_dir / "latest.html"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(latest_content)
    return latest_file

def convert_and_update_library(md_text: str, root_dir_str: str, custom_title: str = None, input_file_path: str = None) -> dict:
    """
    Función principal de compilación y gestión de biblioteca:
    1. Verifica defensivamente la ruta raíz (la crea si no existe o aplica fallback seguro).
    2. Compila el Markdown a HTML con Apple Design y barra de navegación cruzada.
    3. Guarda el nuevo documento.
    4. Genera/actualiza index.html (catálogo más nuevo a más viejo).
    5. Actualiza latest.html.
    6. Retorna diccionario con enlaces, rutas y metadatos.
    """
    # 1. Verificación defensiva de la ruta raíz
    try:
        root_dir = Path(root_dir_str).resolve()
        root_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Fallback seguro a Downloads
        root_dir = (Path.home() / "Downloads" / "Markdown_HTML_Library").resolve()
        root_dir.mkdir(parents=True, exist_ok=True)

    # 2. Parseo de Markdown con detección inteligente de título
    parsed = parse_markdown(md_text, custom_title=custom_title, input_file_path=input_file_path)
    final_title = parsed["title"]

    # Estadísticas
    words = len(re.findall(r'\w+', md_text))
    minutes = max(1, round(words / 190))
    reading_time = f"~{minutes} min de lectura"
    now = datetime.now()
    now_str = now.strftime("%d/%m/%Y %I:%M %p")

    # 3. Determinar nombre de archivo seguro
    if input_file_path and Path(input_file_path).exists() and Path(input_file_path).stem.lower() not in ('temp', 'input', 'a', 'b', 'test', 'tmp', 'untitled', 'document', 'documento'):
        base_slug = slugify(Path(input_file_path).stem)
    else:
        base_slug = slugify(final_title)

    filename = f"{base_slug}.html"
    out_path = root_dir / filename

    # Si existe una colisión y no es del mismo minuto, añadir timestamp
    if out_path.exists():
        time_suffix = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{base_slug}_{time_suffix}.html"
        out_path = root_dir / filename

    # 4. Generar HTML del documento
    html_out = HTML_DOC_TEMPLATE.format(
        title=escape(final_title),
        styles=COMMON_STYLES,
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
        icon_bolt=ICON_BOLT
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    # 5. Generar / actualizar index.html y latest.html
    index_file = generate_index_html(root_dir)
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
        "timestamp": now.strftime("%d/%m/%Y %I:%M %p")
    }

if __name__ == "__main__":
    test_md = """# Documento de Prueba\n\nEste es un documento de prueba para verificar el motor.\n\n- [x] Tarea 1\n- [ ] Tarea 2\n\n> [!NOTE]\n> Nota de prueba."""
    res = convert_and_update_library(test_md, str(Path.home() / "Downloads" / "Markdown_HTML_Library"), "Prueba Inicial")
    print("Resultado:", res)
