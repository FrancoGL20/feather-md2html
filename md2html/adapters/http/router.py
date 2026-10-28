#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Declarative HTTP request router for stdlib BaseHTTPRequestHandler.
Replaces monolithic if/elif chains with a clean route dispatch table.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

RouteHandler = Callable[[Any, Dict[str, Any]], None]


class HttpRouter:
    """Lightweight route dispatcher supporting exact and prefix path matching."""

    def __init__(self) -> None:
        self._exact_routes: Dict[Tuple[str, str], RouteHandler] = {}
        self._prefix_routes: List[Tuple[str, str, RouteHandler]] = []

    def add_route(self, method: str, path: str, handler: RouteHandler) -> None:
        """Registers an exact (method, path) handler."""
        self._exact_routes[(method.upper(), path)] = handler

    def add_prefix_route(self, method: str, prefix: str, handler: RouteHandler) -> None:
        """Registers a prefix-matched handler (e.g., GET /assets/)."""
        self._prefix_routes.append((method.upper(), prefix, handler))

    def get(self, *paths: str) -> Callable[[RouteHandler], RouteHandler]:
        """Decorator for registering GET routes."""

        def decorator(fn: RouteHandler) -> RouteHandler:
            for p in paths:
                self.add_route("GET", p, fn)
            return fn

        return decorator

    def post(self, *paths: str) -> Callable[[RouteHandler], RouteHandler]:
        """Decorator for registering POST routes."""

        def decorator(fn: RouteHandler) -> RouteHandler:
            for p in paths:
                self.add_route("POST", p, fn)
            return fn

        return decorator

    def resolve(self, method: str, path: str) -> Optional[RouteHandler]:
        """Resolves a handler for the given HTTP method and URL path."""
        method_u = method.upper()
        exact = self._exact_routes.get((method_u, path))
        if exact is not None:
            return exact

        for r_method, prefix, handler in self._prefix_routes:
            if r_method == method_u and path.startswith(prefix):
                return handler

        return None
