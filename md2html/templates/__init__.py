#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Presentation templates, CSS stylesheets, SVG icons, and runtime loaders."""

from md2html.templates.icons import (
    ALERT_ICONS,
    ICON_BOLT,
    ICON_CODE,
    ICON_COPY,
    ICON_DIAGRAM,
    ICON_DOC,
    ICON_FOLDER,
    ICON_SEARCH,
)
from md2html.templates.loader import (
    get_catalog_styles,
    get_catalog_template,
    get_common_styles,
    get_html_doc_template,
    get_latest_redirect_template,
    get_math_runtime_code,
    get_math_styles,
    get_mermaid_client_js,
    get_mermaid_runtime_code,
)

__all__ = [
    "ALERT_ICONS",
    "ICON_BOLT",
    "ICON_CODE",
    "ICON_COPY",
    "ICON_DIAGRAM",
    "ICON_DOC",
    "ICON_FOLDER",
    "ICON_SEARCH",
    "get_catalog_styles",
    "get_catalog_template",
    "get_common_styles",
    "get_html_doc_template",
    "get_latest_redirect_template",
    "get_math_runtime_code",
    "get_math_styles",
    "get_mermaid_client_js",
    "get_mermaid_runtime_code",
]
