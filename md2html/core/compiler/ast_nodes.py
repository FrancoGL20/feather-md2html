#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST nodes and stack-based tree builder for nested Markdown lists
(unordered, ordered, and task checklists).
"""

import re
from typing import Any, Dict, List, Tuple

from md2html.core.compiler.inline_parser import inline_formatting


class ListNode:
    """AST container node representing a <ul>, <ol>, or task-list."""

    def __init__(self, list_type: str, start_num: int = 1) -> None:
        self.list_type = list_type  # 'ul', 'ol', 'task'
        self.start_num = start_num
        self.items: List["ItemNode"] = []


class ItemNode:
    """AST node representing an individual <li> item and its nested child lists."""

    def __init__(self, text: str, is_task: bool = False, checked: bool = False) -> None:
        self.text = text
        self.is_task = is_task
        self.checked = checked
        self.children: List[ListNode] = []


def is_list_marker(line: str) -> bool:
    """Checks whether a line begins with a valid unordered, ordered, or task list marker."""
    if not line:
        return False
    clean = line.expandtabs(4)
    stripped = clean.strip()
    if not stripped:
        return False
    if re.match(r"^(?:[-*_]\s*){3,}$", stripped):
        return False
    if re.match(r"^\s*[-*+]\s+\[([ xX])\](?:\s+.*)?$", clean):
        return True
    if re.match(r"^\s*[-*+]\s+(?:.*)?$", clean):
        return True
    if re.match(r"^\s*\d+[\.\)]\s+(?:.*)?$", clean):
        return True
    return False


def render_list_node(node: ListNode) -> str:
    """Renders a ListNode and all its nested descendants to semantic HTML."""
    if node.list_type == "task":
        tag = 'ul class="task-list"'
        close_tag = "ul"
    elif node.list_type == "ol":
        tag = f'ol start="{node.start_num}"' if node.start_num != 1 else "ol"
        close_tag = "ol"
    else:
        tag = "ul"
        close_tag = "ul"

    out = [f"<{tag}>"]
    for it in node.items:
        out.append(render_item_node(it))
    out.append(f"</{close_tag}>")
    return "\n".join(out)


def render_item_node(item: ItemNode) -> str:
    """Renders a single ItemNode and any nested child ListNodes."""
    formatted_text = inline_formatting(item.text)
    if item.is_task:
        chk_attr = " checked" if item.checked else ""
        cls = "task-item checked" if item.checked else "task-item"
        prefix = (
            f'<li class="{cls}"><div class="task-line">'
            f'<input type="checkbox"{chk_attr} disabled> <span>{formatted_text}</span></div>'
        )
    else:
        prefix = f"<li>{formatted_text}"

    if item.children:
        child_htmls = [render_list_node(ch) for ch in item.children]
        return f"{prefix}\n" + "\n".join(child_htmls) + "\n</li>"
    return f"{prefix}</li>"


def parse_list_items(lines: List[str], start_idx: int) -> Tuple[List[Dict[str, Any]], int]:
    """Parses a contiguous block of list lines starting at start_idx."""
    raw_items: List[Dict[str, Any]] = []
    i = start_idx
    n = len(lines)

    while i < n:
        line = lines[i]
        clean = line.expandtabs(4)
        stripped = clean.strip()

        if not stripped:
            peek = i + 1
            while peek < n and not lines[peek].strip():
                peek += 1
            if peek < n and is_list_marker(lines[peek]):
                i += 1
                continue
            break

        if is_list_marker(clean):
            m_task = re.match(r"^(\s*)([-*+])\s+\[([ xX])\](?:\s+(.*)|\s*)$", clean)
            if m_task:
                raw_items.append(
                    {
                        "indent": len(m_task.group(1)),
                        "list_type": "task",
                        "is_task": True,
                        "checked": m_task.group(3).lower() == "x",
                        "text": m_task.group(4) or "",
                        "start_num": 1,
                    }
                )
                i += 1
                continue
            m_ul = re.match(r"^(\s*)([-*+])\s+(.*)$", clean)
            if m_ul:
                raw_items.append(
                    {
                        "indent": len(m_ul.group(1)),
                        "list_type": "ul",
                        "is_task": False,
                        "checked": False,
                        "text": m_ul.group(3),
                        "start_num": 1,
                    }
                )
                i += 1
                continue
            m_ol = re.match(r"^(\s*)(\d+)[\.\)]\s+(.*)$", clean)
            if m_ol:
                raw_items.append(
                    {
                        "indent": len(m_ol.group(1)),
                        "list_type": "ol",
                        "is_task": False,
                        "checked": False,
                        "text": m_ol.group(3),
                        "start_num": int(m_ol.group(2)),
                    }
                )
                i += 1
                continue

        if raw_items and stripped and not stripped.startswith(("#", "```", ">", "|", "---", "===", "***")):
            indent = len(clean) - len(clean.lstrip(" "))
            if indent >= 2:
                raw_items[-1]["text"] += " " + stripped
                i += 1
                continue

        break

    return raw_items, i


def build_tree(raw_items: List[Dict[str, Any]]) -> List[ListNode]:
    """Builds a nested tree of ListNode and ItemNode instances using an indentation stack."""
    if not raw_items:
        return []

    root_lists: List[ListNode] = []
    stack: List[Dict[str, Any]] = []

    for it_data in raw_items:
        indent = it_data["indent"]
        item_node = ItemNode(it_data["text"], it_data["is_task"], it_data["checked"])

        if not stack:
            ln = ListNode(it_data["list_type"], it_data["start_num"])
            ln.items.append(item_node)
            root_lists.append(ln)
            stack.append({"indent": indent, "list_node": ln, "last_item": item_node})
            continue

        while len(stack) > 1 and indent < stack[-1]["indent"]:
            if indent > stack[-2]["indent"]:
                break
            stack.pop()

        top = stack[-1]

        if indent > top["indent"]:
            ln = ListNode(it_data["list_type"], it_data["start_num"])
            ln.items.append(item_node)
            top["last_item"].children.append(ln)
            stack.append({"indent": indent, "list_node": ln, "last_item": item_node})
        else:
            if it_data["list_type"] == top["list_node"].list_type:
                top["list_node"].items.append(item_node)
                top["last_item"] = item_node
            else:
                ln = ListNode(it_data["list_type"], it_data["start_num"])
                ln.items.append(item_node)
                if len(stack) > 1:
                    parent_item = stack[-2]["last_item"]
                    parent_item.children.append(ln)
                else:
                    root_lists.append(ln)
                stack[-1] = {"indent": indent, "list_node": ln, "last_item": item_node}

    return root_lists
