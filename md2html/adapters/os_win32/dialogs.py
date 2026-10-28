#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Native file and directory selection dialogs using standard library tkinter.
"""

from pathlib import Path


def choose_folder_native(initial_dir: str = "") -> str:
    """Opens the native Windows directory picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(
            title="Selecciona la carpeta raíz para guardar los documentos HTML",
            initialdir=initial_dir or str(Path.home() / "Downloads"),
        )
        root.destroy()
        return folder
    except Exception as e:
        print(f"Error abriendo diálogo de carpeta: {e}")
        return ""


def choose_file_native() -> str:
    """Opens the native Windows file picker filtered for Markdown files."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename(
            title="Selecciona un archivo Markdown",
            filetypes=[
                ("Archivos Markdown", "*.md *.markdown *.txt"),
                ("Todos los archivos", "*.*"),
            ],
            initialdir=str(Path.home() / "Downloads"),
        )
        root.destroy()
        return file_path
    except Exception as e:
        print(f"Error abriendo diálogo de archivo: {e}")
        return ""
