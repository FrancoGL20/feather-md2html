#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Test Runner for Markdown to HTML Desktop Application.
Executes the comprehensive test suite with zero external dependencies.
Compatible with standard Python 3.10+ (unittest) and CI/CD pipelines.
"""

import os
import sys
import time
import unittest
from pathlib import Path

# Configure stdout for UTF-8 on Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None):
    try:
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Colors and formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}  MARKDOWN TO HTML DESKTOP APP — SUITE DE PRUEBAS INTEGRAL {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"Directorio de pruebas: {APP_DIR / 'tests'}")
    print(f"Entorno: Python {sys.version.split()[0]} ({sys.platform}) | Zero-Bloatware")
    print(f"----------------------------------------------------------------------\n")


def run_all_tests():
    print_banner()
    start_time = time.time()

    # Discover tests in tests/
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(APP_DIR / "tests"), pattern="test_*.py")

    # Run tests using TextTestRunner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed = time.time() - start_time
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_tests - failures - errors - skipped

    print(f"\n{BOLD}----------------------------------------------------------------------{RESET}")
    print(f"{BOLD}RESUMEN DE EJECUCIÓN DE PRUEBAS:{RESET}")
    print(f"  Total ejecutadas: {BOLD}{total_tests}{RESET}")
    print(f"  {GREEN}✓ Pasadas:{RESET}          {BOLD}{passed}{RESET}")
    if failures > 0:
        print(f"  {RED}✗ Fallos:{RESET}           {BOLD}{failures}{RESET}")
    if errors > 0:
        print(f"  {RED}⚠ Errores:{RESET}          {BOLD}{errors}{RESET}")
    if skipped > 0:
        print(f"  {YELLOW}○ Omitidas:{RESET}         {BOLD}{skipped}{RESET}")
    print(f"  Tiempo total:     {elapsed:.3f} segundos")
    print(f"{BOLD}----------------------------------------------------------------------{RESET}")

    if result.wasSuccessful():
        print(f"\n{BOLD}{GREEN}✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE (100% SUCCESS){RESET}\n")
        return 0
    else:
        print(f"\n{BOLD}{RED}✗ SE ENCONTRARON FALLOS EN LA SUITE DE PRUEBAS{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
