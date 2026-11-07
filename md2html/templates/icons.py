#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inline SVG vector icon definitions used across generated HTML documents."""

from typing import Dict

ICON_DOC = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
    '<polyline points="14 2 14 8 20 8"></polyline>'
    '<line x1="16" y1="13" x2="8" y2="13"></line>'
    '<line x1="16" y1="17" x2="8" y2="17"></line>'
    '<polyline points="10 9 9 9 8 9"></polyline></svg>'
)

ICON_FOLDER = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>'
)

ICON_BOLT = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>'
)

ICON_COPY = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
)

ICON_SEARCH = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="11" cy="11" r="8"></circle>'
    '<line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
)

ICON_DIAGRAM = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="18" cy="5" r="3"></circle>'
    '<circle cx="6" cy="12" r="3"></circle>'
    '<circle cx="18" cy="19" r="3"></circle>'
    '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>'
    '<line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>'
)

ICON_CODE = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="16 18 22 12 16 6"></polyline>'
    '<polyline points="8 6 2 12 8 18"></polyline></svg>'
)

ICON_EXPORT = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
    '<polyline points="7 10 12 15 17 10"></polyline>'
    '<line x1="12" y1="15" x2="12" y2="3"></line></svg>'
)

ICON_EXTERNAL = (
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>'
    '<polyline points="15 3 21 3 21 9"></polyline>'
    '<line x1="10" y1="14" x2="21" y2="3"></line></svg>'
)

ICON_CHEVRON_DOWN = (
    '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="6 9 12 15 18 9"></polyline></svg>'
)

ALERT_ICONS: Dict[str, str] = {
    "note": (
        '<svg viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13z'
        'M6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75z'
        'M8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>'
    ),
    "tip": (
        '<svg viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.677.933.24.437.375.952.375 1.51h3.5'
        'c0-.558.135-1.073.375-1.51.207-.377.454-.669.677-.933l.214-.253c.56-.679.984-1.32.984-2.304 0-2.06-1.637-3.75-4-3.75z'
        'M6 11.75a.75.75 0 0 1 .75-.75h2.5a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1-.75-.75zm.75 2a.75.75 0 0 0 0 1.5h1.5a.75.75 0 0 0 0-1.5h-1.5z"/></svg>'
    ),
    "important": (
        '<svg viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8z'
        'm7.25-3.25a.75.75 0 0 1 1.5 0v3.5a.75.75 0 0 1-1.5 0v-3.5zm.75 6.25a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>'
    ),
    "warning": (
        '<svg viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575L6.457 1.047z'
        'M8 5a.75.75 0 0 0-.75.75v3.5a.75.75 0 0 0 1.5 0v-3.5A.75.75 0 0 0 8 5zm0 7a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/></svg>'
    ),
    "caution": (
        '<svg viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M4.47.04C4.267.014 4.06 0 3.85 0H1.75C.784 0 0 .784 0 1.75v2.1c0 .21.014.417.04.62l1.52 7.6c.14.7.75 1.2 1.46 1.2h9.96'
        'c.71 0 1.32-.5 1.46-1.2l1.52-7.6c.026-.203.04-.41.04-.62V1.75C16 .784 15.216 0 14.25 0h-2.1c-.21 0-.417.014-.62.04L8 1.48 4.47.04z'
        'M8 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 5zm0 7a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>'
    ),
}
