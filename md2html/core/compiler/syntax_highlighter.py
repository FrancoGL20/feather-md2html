#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero-bloatware single-pass lexical syntax highlighter for fenced code blocks.

Tokenizes raw source code prior to HTML escaping using linear-time compiled
regular expressions and emits line-safe <span> elements so client-side
line-wrapping (`initCodeBlocks`) never splits an open tag across newlines.
"""

import html
import re
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple


def _escape(text: str) -> str:
    """HTML-escapes text while keeping single/double quotes readable."""
    return html.escape(text, quote=False)


def _emit_line_safe(out: List[str], token_cls: Optional[str], text: str) -> None:
    """
    Appends escaped HTML for `text` wrapped in `token_cls`, closing and reopening
    the <span> across every newline so every line remains balanced HTML.
    """
    if not text:
        return
    if not token_cls:
        out.append(_escape(text))
        return
    if "\n" not in text:
        out.append(f'<span class="{token_cls}">{_escape(text)}</span>')
        return
    segments = text.split("\n")
    last_idx = len(segments) - 1
    for idx, seg in enumerate(segments):
        if seg:
            out.append(f'<span class="{token_cls}">{_escape(seg)}</span>')
        if idx < last_idx:
            out.append("\n")


_DOLLAR_INTERP_RE = re.compile(
    r"\\[\s\S]|(\$\{[^}\n]+\}|\$\([^)\n]+\)|\$[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)"
)
_PYTHON_FSTRING_INTERP_RE = re.compile(r"\\[\s\S]|\{\{|\}\}|(\{[^}\n]+\})")
_RUBY_INTERP_RE = re.compile(r"\\[\s\S]|(#\{[^}\n]+\})")


def _emit_interpolated_string(
    out: List[str],
    text: str,
    interp_re: re.Pattern,
) -> None:
    """Highlights string literals containing inline variable interpolations."""
    pos = 0
    for m in interp_re.finditer(text):
        expr = m.group(1)
        if not expr:
            continue
        if m.start() > pos:
            _emit_line_safe(out, "tok-str", text[pos : m.start()])
        _emit_line_safe(out, "tok-var", expr)
        pos = m.end()
    if pos < len(text):
        _emit_line_safe(out, "tok-str", text[pos:])


_MARKUP_TAG_SPLIT_RE = re.compile(r"^(\s*</?)([A-Za-z][A-Za-z0-9:._-]*)([\s\S]*?)(/?>)$")
_MARKUP_ATTR_RE = re.compile(
    r'("(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\')'
    r"|([A-Za-z_:][A-Za-z0-9_:.-]*)(?=\s*=)"
    r"|(=)"
)


def _emit_markup_tag(out: List[str], text: str) -> None:
    """Highlights an HTML/XML tag while keeping delimiters, attributes, and values line-safe."""
    m = _MARKUP_TAG_SPLIT_RE.match(text)
    if not m:
        _emit_line_safe(out, "tok-tag", text)
        return
    open_delim, tag_name, attr_body, close_delim = m.groups()
    _emit_line_safe(out, "tok-op", open_delim)
    _emit_line_safe(out, "tok-tag", tag_name)
    if attr_body:
        pos = 0
        for am in _MARKUP_ATTR_RE.finditer(attr_body):
            if am.start() > pos:
                _emit_line_safe(out, None, attr_body[pos : am.start()])
            if am.group(1):
                _emit_line_safe(out, "tok-str", am.group(1))
            elif am.group(2):
                _emit_line_safe(out, "tok-attr", am.group(2))
            elif am.group(3):
                _emit_line_safe(out, "tok-op", am.group(3))
            pos = am.end()
        if pos < len(attr_body):
            _emit_line_safe(out, None, attr_body[pos:])
    _emit_line_safe(out, "tok-op", close_delim)


def _emit_yaml_key(out: List[str], text: str) -> None:
    """Highlights a YAML mapping key while preserving leading indentation and `- ` markers."""
    m = re.match(r"^([ \t]*)(-\s+)?([\s\S]+)$", text)
    if not m:
        _emit_line_safe(out, "tok-attr", text)
        return
    indent, dash, key = m.groups()
    if indent:
        _emit_line_safe(out, None, indent)
    if dash:
        _emit_line_safe(out, "tok-op", dash)
    _emit_line_safe(out, "tok-attr", key)


def _emit_ini_key(out: List[str], text: str) -> None:
    """Highlights an INI/properties key name and its `=`/` :` separator."""
    m = re.match(r"^([ \t]*)([^:=\s][^:=\n]*?)([ \t]*[:=])", text)
    if not m:
        _emit_line_safe(out, "tok-attr", text)
        return
    indent, key, sep = m.groups()
    if indent:
        _emit_line_safe(out, None, indent)
    _emit_line_safe(out, "tok-attr", key)
    _emit_line_safe(out, "tok-op", sep)


@dataclass(frozen=True)
class TokenRule:
    """Single lexical rule matching a token class or custom emitter callback."""

    token_cls: Optional[str]
    pattern: str
    emitter: Optional[Callable[[List[str], str], None]] = None


@dataclass(frozen=True)
class LanguageSpec:
    """Compiled specification for a language grammar."""

    master_re: re.Pattern
    group_rules: Dict[str, TokenRule]


def _compile_spec(rules: List[TokenRule], flags: int = re.MULTILINE) -> LanguageSpec:
    """Compiles an ordered list of TokenRules into a single master regex."""
    group_rules: Dict[str, TokenRule] = {}
    parts: List[str] = []
    for idx, rule in enumerate(rules):
        gname = f"T{idx}"
        group_rules[gname] = rule
        parts.append(f"(?P<{gname}>{rule.pattern})")
    return LanguageSpec(
        master_re=re.compile("|".join(parts), flags),
        group_rules=group_rules,
    )


def _highlight_with_spec(code_raw: str, spec: LanguageSpec) -> str:
    """Single-pass tokenization over `code_raw` using a compiled LanguageSpec."""
    out: List[str] = []
    pos = 0
    for m in spec.master_re.finditer(code_raw):
        if m.start() > pos:
            _emit_line_safe(out, None, code_raw[pos : m.start()])
        gname = m.lastgroup
        if gname:
            rule = spec.group_rules[gname]
            text = m.group(gname)
            if rule.emitter is not None:
                rule.emitter(out, text)
            else:
                _emit_line_safe(out, rule.token_cls, text)
        pos = m.end()
    if pos < len(code_raw):
        _emit_line_safe(out, None, code_raw[pos:])
    return "".join(out)


# ---------------------------------------------------------------------------
# Specialized Highlighters (Diff & Gherkin)
# ---------------------------------------------------------------------------

def _highlight_diff(code_raw: str) -> str:
    """Highlights unified diff/patch blocks while preserving +/- line classes."""
    out: List[str] = []
    lines = code_raw.split("\n")
    last_idx = len(lines) - 1
    for idx, line in enumerate(lines):
        if line.startswith(("diff --git", "index ", "+++ ", "--- ")):
            _emit_line_safe(out, "tok-comment", line)
        elif line.startswith("@@"):
            m = re.match(r"^(@@[^@]*@@)([\s\S]*)$", line)
            if m:
                _emit_line_safe(out, "tok-const", m.group(1))
                _emit_line_safe(out, "tok-comment", m.group(2))
            else:
                _emit_line_safe(out, "tok-const", line)
        elif line.startswith("+"):
            _emit_line_safe(out, "tok-diff-add", line)
        elif line.startswith("-"):
            _emit_line_safe(out, "tok-diff-del", line)
        else:
            _emit_line_safe(out, None, line)
        if idx < last_idx:
            out.append("\n")
    return "".join(out)


_GHERKIN_HEADER_RE = re.compile(
    r"^([ \t]*)"
    r"(Scenario Outline|Scenario Template|Esquema del escenario|"
    r"Feature|Rule|Background|Scenario|Examples|"
    r"Caracter[ií]stica|Regla|Antecedentes|Escenario|Ejemplos)"
    r"(:)([\s\S]*)$",
    re.IGNORECASE,
)
_GHERKIN_STEP_RE = re.compile(
    r"^([ \t]*)"
    r"(Given|When|Then|And|But|Dado|Dada|Dados|Dadas|Cuando|Entonces|Y|E|Pero|\*)"
    r"(?=[ \t]|$)([\s\S]*)$",
    re.IGNORECASE,
)
_GHERKIN_INLINE_RE = re.compile(
    r'(?P<str>"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\')'
    r"|(?P<placeholder><[^>\n]+>)"
    r"|(?P<pipe>\|)"
    r"|(?P<num>\b\d+(?:\.\d+)?\b)"
)
_GHERKIN_STR_PLACEHOLDER_RE = re.compile(r"<[^>\n\"']+>")
_GHERKIN_TAG_RE = re.compile(r"@[^\s@#]+")


def _emit_gherkin_string(out: List[str], text: str) -> None:
    """Highlights Gherkin string literals and any Scenario Outline <placeholder> inside them."""
    pos = 0
    for m in _GHERKIN_STR_PLACEHOLDER_RE.finditer(text):
        if m.start() > pos:
            _emit_line_safe(out, "tok-str", text[pos : m.start()])
        _emit_line_safe(out, "tok-const", m.group(0))
        pos = m.end()
    if pos < len(text):
        _emit_line_safe(out, "tok-str", text[pos:])


def _emit_gherkin_inline(out: List[str], text: str) -> None:
    """Highlights strings, outline <placeholders>, table pipes, and numbers inside Gherkin."""
    pos = 0
    for m in _GHERKIN_INLINE_RE.finditer(text):
        if m.start() > pos:
            _emit_line_safe(out, None, text[pos : m.start()])
        gname = m.lastgroup
        if gname == "str":
            _emit_gherkin_string(out, m.group(gname))
        elif gname == "placeholder":
            _emit_line_safe(out, "tok-const", m.group(gname))
        elif gname == "pipe":
            _emit_line_safe(out, "tok-op", m.group(gname))
        elif gname == "num":
            _emit_line_safe(out, "tok-num", m.group(gname))
        pos = m.end()
    if pos < len(text):
        _emit_line_safe(out, None, text[pos:])


def _highlight_gherkin(code_raw: str) -> str:
    """Line-oriented lexical highlighter for Gherkin (.feature) in English and Spanish."""
    out: List[str] = []
    lines = code_raw.split("\n")
    last_idx = len(lines) - 1
    in_docstring = False
    docstring_delim = '"""'

    for idx, line in enumerate(lines):
        stripped = line.strip()

        if in_docstring:
            _emit_line_safe(out, "tok-str", line)
            if stripped.startswith(docstring_delim):
                in_docstring = False
        elif stripped.startswith(('"""', "```")):
            docstring_delim = '"""' if stripped.startswith('"""') else "```"
            in_docstring = True
            _emit_line_safe(out, "tok-str", line)
        elif stripped.startswith("#"):
            _emit_line_safe(out, "tok-comment", line)
        elif stripped.startswith("@"):
            pos = 0
            for tm in _GHERKIN_TAG_RE.finditer(line):
                if tm.start() > pos:
                    _emit_line_safe(out, None, line[pos : tm.start()])
                _emit_line_safe(out, "tok-tag", tm.group(0))
                pos = tm.end()
            if pos < len(line):
                remainder = line[pos:]
                comment_idx = remainder.find("#")
                if comment_idx != -1:
                    _emit_line_safe(out, None, remainder[:comment_idx])
                    _emit_line_safe(out, "tok-comment", remainder[comment_idx:])
                else:
                    _emit_line_safe(out, None, remainder)
        elif stripped.startswith("|"):
            _emit_gherkin_inline(out, line)
        else:
            m_hdr = _GHERKIN_HEADER_RE.match(line)
            m_step = None if m_hdr else _GHERKIN_STEP_RE.match(line)
            if m_hdr:
                indent, kw, colon, rest = m_hdr.groups()
                _emit_line_safe(out, None, indent)
                _emit_line_safe(out, "tok-kw", kw + colon)
                _emit_gherkin_inline(out, rest)
            elif m_step:
                indent, step_kw, rest = m_step.groups()
                _emit_line_safe(out, None, indent)
                _emit_line_safe(out, "tok-step", step_kw)
                _emit_gherkin_inline(out, rest)
            else:
                _emit_gherkin_inline(out, line)

        if idx < last_idx:
            out.append("\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Reusable Token Building Blocks & Declarative Language Registry
# ---------------------------------------------------------------------------

_STR_DQ = r'"(?:\\[\s\S]|[^"\\])*"'
_STR_SQ = r"'(?:\\[\s\S]|[^'\\])*'"
_STR_BT = r"`(?:\\[\s\S]|[^`\\])*`"
_STR_TDQ = r'"""[\s\S]*?"""'
_STR_TSQ = r"'''[\s\S]*?'''"
_CMT_SLASH = r"//[^\n]*"
_CMT_HASH = r"#[^\n]*"
_CMT_BLOCK = r"/\*[\s\S]*?\*/"
_NUM_STD = r"\b(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?)[uUlLfFdDgG]?\b"
_FN_CALL = r"\b[a-z_][A-Za-z0-9_]*(?=\s*\()"
_PASCAL_TYPE = r"\b[A-Z][A-Za-z0-9_]*\b"
_UPPER_CONST = r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b"
_OP_COMMON = r"=>|->|::|===|!==|==~|=~|\?\?|\?\.|&&|\|\||<=|>=|<<|>>"


def _emit_dollar_string(out: List[str], text: str) -> None:
    """Emits a string literal with $var / ${expr} / $(...) interpolation."""
    _emit_interpolated_string(out, text, _DOLLAR_INTERP_RE)


def _emit_py_fstring(out: List[str], text: str) -> None:
    """Emits a Python f-string literal with {expr} interpolation."""
    _emit_interpolated_string(out, text, _PYTHON_FSTRING_INTERP_RE)


def _emit_ruby_string(out: List[str], text: str) -> None:
    """Emits a Ruby double-quoted string with #{expr} interpolation."""
    _emit_interpolated_string(out, text, _RUBY_INTERP_RE)


def _c_like_spec(
    keywords: str,
    constants: str,
    builtin_types: str,
    *,
    annotations: bool = True,
    backtick_interp: bool = False,
    double_interp: bool = False,
    triple_strings: bool = False,
    hash_comments: bool = False,
    extra_rules: Optional[List[TokenRule]] = None,
) -> LanguageSpec:
    """Builds a LanguageSpec for C/JVM/JS-family languages."""
    rules: List[TokenRule] = [
        TokenRule("tok-comment", _CMT_BLOCK),
        TokenRule("tok-comment", _CMT_SLASH),
    ]
    if hash_comments:
        rules.append(TokenRule("tok-comment", _CMT_HASH))
    if triple_strings:
        rules.append(TokenRule("tok-str", _STR_TDQ, _emit_dollar_string if double_interp else None))
        rules.append(TokenRule("tok-str", _STR_TSQ))
    if backtick_interp:
        rules.append(TokenRule("tok-str", _STR_BT, _emit_dollar_string))
    else:
        rules.append(TokenRule("tok-str", _STR_BT))
    rules.append(TokenRule("tok-str", _STR_DQ, _emit_dollar_string if double_interp else None))
    rules.append(TokenRule("tok-str", _STR_SQ))
    if extra_rules:
        rules.extend(extra_rules)
    if annotations:
        rules.append(TokenRule("tok-tag", r"@[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"))
    rules.extend(
        [
            TokenRule("tok-kw", rf"\b(?:{keywords})\b"),
            TokenRule("tok-const", rf"\b(?:{constants})\b"),
            TokenRule("tok-const", _UPPER_CONST),
        ]
    )
    if builtin_types:
        rules.append(TokenRule("tok-type", rf"\b(?:{builtin_types})\b"))
    rules.extend(
        [
            TokenRule("tok-type", _PASCAL_TYPE),
            TokenRule("tok-fn", _FN_CALL),
            TokenRule("tok-num", _NUM_STD),
            TokenRule("tok-op", _OP_COMMON),
        ]
    )
    return _compile_spec(rules)


def _build_specs() -> Dict[str, LanguageSpec]:
    """Constructs and caches the compiled LanguageSpec table for all built-in languages."""
    specs: Dict[str, LanguageSpec] = {}

    specs["groovy"] = _c_like_spec(
        keywords=(
            "def|trait|in|as|assert|class|interface|enum|extends|implements|package|import|"
            "static|final|abstract|public|private|protected|synchronized|transient|volatile|"
            "if|else|for|while|do|switch|case|default|break|continue|return|try|catch|finally|"
            "throw|throws|new|instanceof|void"
        ),
        constants="true|false|null|this|super|it",
        builtin_types="boolean|byte|short|char|int|long|float|double",
        annotations=True,
        double_interp=True,
        triple_strings=True,
    )

    specs["java"] = _c_like_spec(
        keywords=(
            "class|interface|enum|record|extends|implements|permits|sealed|non-sealed|package|import|"
            "static|final|abstract|public|private|protected|synchronized|transient|volatile|native|"
            "if|else|for|while|do|switch|case|default|break|continue|return|try|catch|finally|"
            "throw|throws|new|instanceof|void|var|yield|assert"
        ),
        constants="true|false|null|this|super",
        builtin_types="boolean|byte|short|char|int|long|float|double",
        annotations=True,
        triple_strings=True,
    )

    specs["kotlin"] = _c_like_spec(
        keywords=(
            "fun|val|var|class|interface|object|enum|data|sealed|open|abstract|override|companion|"
            "package|import|private|protected|public|internal|inline|suspend|reified|lateinit|by|"
            "if|else|when|for|while|do|in|is|as|return|break|continue|try|catch|finally|throw|init|"
            "constructor|where|typealias"
        ),
        constants="true|false|null|this|super|it",
        builtin_types="Unit|Nothing|Any|Boolean|Byte|Short|Int|Long|Float|Double|String|Char",
        annotations=True,
        double_interp=True,
        triple_strings=True,
    )

    specs["csharp"] = _c_like_spec(
        keywords=(
            "namespace|using|class|struct|interface|enum|record|delegate|event|public|private|"
            "protected|internal|static|readonly|const|virtual|override|abstract|sealed|partial|"
            "async|await|var|dynamic|if|else|switch|case|default|for|foreach|in|while|do|break|"
            "continue|return|yield|try|catch|finally|throw|new|is|as|typeof|nameof|sizeof|params|"
            "ref|out|void|get|set|init|required"
        ),
        constants="true|false|null|this|base",
        builtin_types="bool|byte|sbyte|char|decimal|double|float|int|uint|long|ulong|short|ushort|object|string|nint|nuint",
        annotations=False,
        extra_rules=[
            TokenRule("tok-str", r'\$@"(?:""|[^"])*"', _emit_py_fstring),
            TokenRule("tok-str", r'@"(?:""|[^"])*"'),
            TokenRule("tok-str", rf'\$"{_STR_DQ[1:]}', _emit_py_fstring),
            TokenRule("tok-tag", r"\[[A-Za-z_][A-Za-z0-9_.]*(?:\([^)\n]*\))?\]"),
        ],
    )

    js_keywords = (
        "function|const|let|var|return|if|else|for|while|do|switch|case|default|break|continue|"
        "try|catch|finally|throw|class|extends|new|import|from|export|default|async|await|yield|"
        "typeof|instanceof|in|of|delete|void|static|get|set|debugger"
    )
    js_constants = "true|false|null|undefined|NaN|Infinity|this|super"
    specs["javascript"] = _c_like_spec(
        keywords=js_keywords,
        constants=js_constants,
        builtin_types="",
        annotations=True,
        backtick_interp=True,
    )

    specs["typescript"] = _c_like_spec(
        keywords=(
            f"{js_keywords}|interface|type|enum|implements|namespace|declare|module|readonly|"
            "public|private|protected|abstract|override|keyof|infer|is|as|satisfies|asserts"
        ),
        constants=js_constants,
        builtin_types="string|number|boolean|symbol|bigint|object|any|unknown|never|void",
        annotations=True,
        backtick_interp=True,
    )

    specs["go"] = _c_like_spec(
        keywords=(
            "package|import|func|var|const|type|struct|interface|map|chan|go|defer|select|"
            "if|else|for|range|switch|case|default|break|continue|return|fallthrough|goto"
        ),
        constants="true|false|nil|iota",
        builtin_types=(
            "bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|"
            "rune|string|uint|uint8|uint16|uint32|uint64|uintptr|any|comparable"
        ),
        annotations=False,
    )

    specs["rust"] = _c_like_spec(
        keywords=(
            "fn|let|mut|const|static|pub|crate|super|mod|use|struct|enum|union|impl|trait|type|"
            "where|for|in|loop|while|if|else|match|break|continue|return|async|await|move|ref|"
            "unsafe|extern|dyn|as"
        ),
        constants="true|false|self|Self|Some|None|Ok|Err",
        builtin_types="bool|char|str|i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize|f32|f64",
        annotations=False,
        extra_rules=[
            TokenRule("tok-tag", r"#!?\[[\s\S]*?\]"),
            TokenRule("tok-fn", r"\b[a-z_][A-Za-z0-9_]*!"),
            TokenRule("tok-tag", r"'[a-z_][A-Za-z0-9_]*\b"),
        ],
    )

    specs["cpp"] = _c_like_spec(
        keywords=(
            "auto|break|case|catch|class|const|constexpr|consteval|continue|default|delete|do|"
            "else|enum|explicit|export|extern|for|friend|goto|if|inline|mutable|namespace|new|"
            "noexcept|operator|private|protected|public|register|return|sizeof|static|static_cast|"
            "dynamic_cast|reinterpret_cast|const_cast|struct|switch|template|throw|try|typedef|"
            "typename|union|using|virtual|volatile|while|co_await|co_return|co_yield|concept|requires"
        ),
        constants="true|false|nullptr|NULL|this",
        builtin_types="void|bool|char|wchar_t|char8_t|char16_t|char32_t|short|int|long|float|double|signed|unsigned|size_t",
        annotations=False,
        extra_rules=[
            TokenRule("tok-step", r"^[ \t]*#[A-Za-z_][A-Za-z0-9_]*"),
            TokenRule("tok-str", r"(?<=#include)[ \t]+<[^>\n]+>"),
        ],
    )

    specs["php"] = _c_like_spec(
        keywords=(
            "function|fn|class|interface|trait|enum|extends|implements|namespace|use|public|"
            "private|protected|static|final|abstract|readonly|const|if|elseif|else|for|foreach|"
            "as|while|do|switch|case|default|match|break|continue|return|try|catch|finally|throw|"
            "new|instanceof|echo|print|require|require_once|include|include_once|yield|global"
        ),
        constants="true|false|null|TRUE|FALSE|NULL",
        builtin_types="int|float|string|bool|array|object|callable|iterable|mixed|void|never",
        annotations=False,
        hash_comments=True,
        double_interp=True,
        extra_rules=[
            TokenRule("tok-step", r"<\?(?:php|=)?|\?>"),
            TokenRule("tok-var", r"\$[A-Za-z_][A-Za-z0-9_]*"),
        ],
    )

    specs["python"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-str", rf'[rRbBuU]?[fF][rRbBuU]?(?:{_STR_TDQ}|{_STR_TSQ}|{_STR_DQ}|{_STR_SQ})', _emit_py_fstring),
            TokenRule("tok-str", rf'(?:[rRbBuU]{{1,2}})?(?:{_STR_TDQ}|{_STR_TSQ}|{_STR_DQ}|{_STR_SQ})'),
            TokenRule("tok-tag", r"^[ \t]*@[A-Za-z_][A-Za-z0-9_.]*"),
            TokenRule(
                "tok-kw",
                r"\b(?:def|class|return|import|from|as|if|elif|else|for|while|break|continue|"
                r"try|except|finally|raise|with|pass|lambda|yield|async|await|global|nonlocal|"
                r"del|assert|match|case|and|or|not|is|in)\b",
            ),
            TokenRule("tok-const", r"\b(?:True|False|None|self|cls|Ellipsis|NotImplemented)\b"),
            TokenRule("tok-const", _UPPER_CONST),
            TokenRule(
                "tok-type",
                r"\b(?:int|float|str|bool|list|dict|set|tuple|bytes|object|type|Any|Optional|"
                r"Union|List|Dict|Set|Tuple|Callable|Sequence|Mapping)\b",
            ),
            TokenRule("tok-type", _PASCAL_TYPE),
            TokenRule("tok-fn", _FN_CALL),
            TokenRule("tok-num", _NUM_STD),
            TokenRule("tok-op", _OP_COMMON),
        ]
    )

    specs["ruby"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-str", _STR_DQ, _emit_ruby_string),
            TokenRule("tok-str", _STR_SQ),
            TokenRule("tok-var", r"(?:@@?|\$)[A-Za-z_][A-Za-z0-9_]*"),
            TokenRule("tok-tag", r":[A-Za-z_][A-Za-z0-9_?!]*"),
            TokenRule(
                "tok-kw",
                r"\b(?:def|end|class|module|if|elsif|else|unless|case|when|while|until|for|in|"
                r"do|begin|rescue|ensure|raise|return|yield|break|next|redo|retry|require|"
                r"require_relative|include|extend|attr_accessor|attr_reader|attr_writer|and|or|not)\b",
            ),
            TokenRule("tok-const", r"\b(?:true|false|nil|self|super|__FILE__|__LINE__)\b"),
            TokenRule("tok-type", _PASCAL_TYPE),
            TokenRule("tok-fn", _FN_CALL),
            TokenRule("tok-num", _NUM_STD),
            TokenRule("tok-op", _OP_COMMON),
        ]
    )

    specs["powershell"] = _compile_spec(
        [
            TokenRule("tok-comment", r"<#[\s\S]*?#>"),
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-str", r'@"[\s\S]*?"@', _emit_dollar_string),
            TokenRule("tok-str", r"@'[\s\S]*?'@"),
            TokenRule("tok-str", _STR_DQ, _emit_dollar_string),
            TokenRule("tok-str", _STR_SQ),
            TokenRule(
                "tok-kw",
                r"(?<![\\/.A-Za-z0-9_-])(?:function|filter|workflow|param|begin|process|end|if|elseif|else|"
                r"foreach|for|while|do|until|switch|break|continue|try|catch|finally|trap|"
                r"return|throw|in|class|enum|using)(?![\\/.A-Za-z0-9_-])",
            ),
            TokenRule("tok-const", r"\$(?:true|false|null)\b"),
            TokenRule("tok-var", r"\$\{[^}\n]+\}|\$(?:[A-Za-z_][A-Za-z0-9_:]*|_)"),
            TokenRule(
                "tok-op",
                r"(?<!\w)-(?:eq|ne|gt|lt|ge|le|like|notlike|match|notmatch|"
                r"contains|notcontains|in|notin|replace|split|join|and|or|xor|not|is|isnot|as)\b",
            ),
            TokenRule("tok-fn", r"(?<![\\/.A-Za-z0-9_-])[A-Za-z]+-[A-Za-z][A-Za-z0-9]*(?![\\/.A-Za-z0-9_-])"),
            TokenRule("tok-attr", r"(?<!\w)-[A-Za-z][A-Za-z0-9_]*\b"),
            TokenRule("tok-type", r"\[[A-Za-z_][A-Za-z0-9_.\[\]]*\]"),
            TokenRule("tok-num", _NUM_STD),
            TokenRule("tok-op", r"\||=>|="),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["bash"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-str", _STR_DQ, _emit_dollar_string),
            TokenRule("tok-str", _STR_SQ),
            TokenRule("tok-var", r"\$\{[^}\n]+\}|\$\([^)\n]+\)|\$[A-Za-z_?@*#!0-9][A-Za-z0-9_]*"),
            TokenRule(
                "tok-kw",
                r"(?<![\\/.A-Za-z0-9_-])(?:if|then|elif|else|fi|for|in|do|done|case|esac|while|until|select|"
                r"function|time|export|local|readonly|declare|typeset|unset|return|exit|source|alias)(?![\\/.A-Za-z0-9_-])",
            ),
            TokenRule(
                "tok-fn",
                r"(?<![\\/.A-Za-z0-9_-])(?:echo|printf|cd|pwd|ls|dir|cat|head|tail|grep|rg|sed|awk|find|sort|uniq|"
                r"mkdir|rmdir|rm|cp|mv|touch|chmod|chown|ln|curl|wget|tar|zip|unzip|"
                r"git|docker|docker-compose|kubectl|python|python3|pip|npm|npx|node|java|gradle|mvn|"
                r"pwsh|powershell|sudo|test|true|false)(?![\\/.A-Za-z0-9_-])",
            ),
            TokenRule("tok-attr", r"(?<!\w)--?[A-Za-z0-9][A-Za-z0-9_-]*"),
            TokenRule("tok-num", r"\b\d+\b"),
            TokenRule("tok-op", r"&&|\|\||>>|<<|2>&1|[|&;<>]"),
        ]
    )

    specs["bat"] = _compile_spec(
        [
            TokenRule("tok-comment", r"^[ \t]*(?:rem\b[^\n]*|::[^\n]*)"),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-var", r"%[A-Za-z_0-9~*]+%|![A-Za-z_0-9]+!"),
            TokenRule("tok-tag", r"^[ \t]*:[A-Za-z_][A-Za-z0-9_-]*"),
            TokenRule(
                "tok-kw",
                r"@?\b(?:echo|off|on|set|setlocal|endlocal|if|else|exist|defined|not|"
                r"for|in|do|call|goto|exit|start|pause|cd|pushd|popd|mkdir|rmdir|copy|xcopy|robocopy|del)\b",
            ),
            TokenRule("tok-attr", r"(?<!\w)/[A-Za-z0-9?]+"),
            TokenRule("tok-num", r"\b\d+\b"),
            TokenRule("tok-op", r"&&|\|\||>>|[|&<>]"),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["json"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_BLOCK),
            TokenRule("tok-comment", _CMT_SLASH),
            TokenRule("tok-attr", rf'{_STR_DQ}(?=\s*:)'),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-const", r"\b(?:true|false|null)\b"),
            TokenRule("tok-num", r"-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
            TokenRule("tok-op", r"[\{\}\[\]:,]"),
        ]
    )

    specs["yaml"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-op", r"^[ \t]*(?:---|\.\.\.)(?=[ \t]*$)"),
            TokenRule(
                "tok-attr",
                r'^[ \t]*(?:-[ \t]+)?(?:"[^"\n]+"|\'[^\'\n]+\'|[A-Za-z0-9_./-]+)(?=[ \t]*:(?:[ \t]|$))',
                _emit_yaml_key,
            ),
            TokenRule("tok-str", _STR_DQ, _emit_dollar_string),
            TokenRule("tok-str", _STR_SQ),
            TokenRule("tok-tag", r"(?:&|\*|!!)[A-Za-z0-9_.-]+"),
            TokenRule("tok-var", r"\$\{[^}\n]+\}|\{\{[^}\n]+\}\}"),
            TokenRule(
                "tok-const",
                r"(?<=[:\-\[\{,\s])(?:true|false|yes|no|on|off|null|~)(?=[ \t]*(?:#|,|\]|\}|$))",
            ),
            TokenRule("tok-num", r"(?<=[:\-\[\{,\s])-?\d+(?:\.\d+)?(?=[ \t]*(?:#|,|\]|\}|$))"),
            TokenRule("tok-op", r"^[ \t]*-(?=[ \t]+)|[:\[\]\{\}\|>]"),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["toml"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-tag", r"^[ \t]*\[{1,2}[^\]\n]+\]{1,2}"),
            TokenRule("tok-str", _STR_TDQ),
            TokenRule("tok-str", _STR_TSQ),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-str", _STR_SQ),
            TokenRule("tok-attr", r"^[ \t]*[A-Za-z0-9_.-]+(?=[ \t]*=)"),
            TokenRule("tok-const", r"\b(?:true|false)\b"),
            TokenRule("tok-num", r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)?\b"),
            TokenRule("tok-num", _NUM_STD),
        ]
    )

    specs["ini"] = _compile_spec(
        [
            TokenRule("tok-comment", r"^[ \t]*[#;][^\n]*"),
            TokenRule("tok-tag", r"^[ \t]*\[[^\]\n]+\]"),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-str", _STR_SQ),
            TokenRule("tok-attr", r"^[ \t]*[^:=\s#;\n][^:=\n]*?[ \t]*[:=]", _emit_ini_key),
            TokenRule("tok-const", r"\b(?:true|false|yes|no|on|off|null)\b"),
            TokenRule("tok-num", r"\b\d+(?:\.\d+)?\b"),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["sql"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_BLOCK),
            TokenRule("tok-comment", r"--[^\n]*"),
            TokenRule("tok-str", r"'(?:''|[^'])*'"),
            TokenRule("tok-attr", r'"(?:""|[^"])*"|`[^`\n]+`'),
            TokenRule(
                "tok-kw",
                r"\b(?:SELECT|DISTINCT|TOP|FROM|WHERE|AND|OR|NOT|IN|IS|BETWEEN|LIKE|ILIKE|SIMILAR|"
                r"EXISTS|JOIN|INNER|LEFT|RIGHT|FULL|OUTER|CROSS|NATURAL|ON|USING|AS|GROUP|BY|"
                r"HAVING|ORDER|ASC|DESC|NULLS|FIRST|LAST|LIMIT|OFFSET|FETCH|NEXT|ROWS|ONLY|"
                r"INSERT|INTO|VALUES|UPDATE|SET|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|"
                r"TABLE|VIEW|INDEX|SEQUENCE|DATABASE|SCHEMA|TRIGGER|FUNCTION|PROCEDURE|"
                r"IF|CASE|WHEN|THEN|ELSE|END|UNION|INTERSECT|EXCEPT|ALL|WITH|RECURSIVE|"
                r"RETURNING|PRIMARY|KEY|FOREIGN|REFERENCES|DEFAULT|UNIQUE|CHECK|CONSTRAINT|"
                r"BEGIN|COMMIT|ROLLBACK|TRANSACTION|SAVEPOINT|GRANT|REVOKE|EXPLAIN|ANALYZE)\b",
            ),
            TokenRule("tok-const", r"\b(?:NULL|TRUE|FALSE|CURRENT_TIMESTAMP|CURRENT_DATE|CURRENT_TIME|CURRENT_USER)\b"),
            TokenRule(
                "tok-fn",
                r"\b(?:COUNT|SUM|AVG|MIN|MAX|COALESCE|NULLIF|CAST|CONVERT|LOWER|UPPER|TRIM|"
                r"LENGTH|CHAR_LENGTH|SUBSTRING|CONCAT|REPLACE|NOW|DATE_TRUNC|EXTRACT|"
                r"ROW_NUMBER|RANK|DENSE_RANK|LAG|LEAD|OVER|PARTITION)\b(?=\s*\()",
            ),
            TokenRule("tok-num", _NUM_STD),
            TokenRule("tok-op", r"<>|!=|<=|>=|\|\||::|[=<>+\-*/(),.;]"),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["html"] = _compile_spec(
        [
            TokenRule("tok-comment", r"<!--[\s\S]*?-->"),
            TokenRule("tok-tag", r"<!DOCTYPE[^>]*>"),
            TokenRule("tok-str", r"<!\[CDATA\[[\s\S]*?\]\]>"),
            TokenRule("tok-tag", r"<\?xml[\s\S]*?\?>"),
            TokenRule(
                "tok-tag",
                r'</?[A-Za-z][A-Za-z0-9:._-]*(?=\s|/?>)(?:[^>"\']|"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\')*/?>',
                _emit_markup_tag,
            ),
            TokenRule("tok-const", r"&(?:[A-Za-z]+|#\d+|#x[0-9a-fA-F]+);"),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["css"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_BLOCK),
            TokenRule("tok-comment", _CMT_SLASH),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-str", _STR_SQ),
            TokenRule("tok-step", r"@[a-zA-Z-]+"),
            TokenRule("tok-kw", r"!important\b"),
            TokenRule("tok-var", r"--[A-Za-z0-9_-]+"),
            TokenRule("tok-const", r"#[0-9a-fA-F]{3,8}\b"),
            TokenRule("tok-fn", r"[a-zA-Z_-][A-Za-z0-9_-]*(?=\()"),
            TokenRule("tok-attr", r"\b[a-z][a-z0-9-]*(?=\s*:)"),
            TokenRule("tok-tag", r"(?:\.[A-Za-z_][A-Za-z0-9_-]*|#[A-Za-z_][A-Za-z0-9_-]*|::?[A-Za-z-]+)"),
            TokenRule("tok-num", r"(?<![A-Za-z0-9_-])-?\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw|vmin|vmax|ch|ms|s|deg|rad|fr)?(?![A-Za-z0-9_])"),
            TokenRule("tok-op", r"[\{\}:;,\(\)>+~]"),
        ]
    )

    specs["dockerfile"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-str", _STR_DQ, _emit_dollar_string),
            TokenRule("tok-str", _STR_SQ),
            TokenRule(
                "tok-kw",
                r"^[ \t]*(?:FROM|AS|RUN|CMD|LABEL|MAINTAINER|EXPOSE|ENV|ADD|COPY|ENTRYPOINT|"
                r"VOLUME|USER|WORKDIR|ARG|ONBUILD|STOPSIGNAL|HEALTHCHECK|SHELL)\b",
            ),
            TokenRule("tok-attr", r"(?<!\w)--[A-Za-z0-9-]+=?"),
            TokenRule("tok-var", r"\$\{[^}\n]+\}|\$[A-Za-z_][A-Za-z0-9_]*"),
            TokenRule("tok-num", r"\b\d+\b"),
        ],
        flags=re.MULTILINE | re.IGNORECASE,
    )

    specs["http"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-kw", r"^[ \t]*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|TRACE|CONNECT)\b"),
            TokenRule("tok-step", r"\bHTTP/\d(?:\.\d)?\b"),
            TokenRule("tok-attr", r"^[ \t]*[A-Za-z][A-Za-z0-9-]*(?=:)"),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-tag", r"https?://[^\s]+"),
            TokenRule("tok-num", r"\b[1-5]\d{2}\b"),
        ]
    )

    specs["graphql"] = _compile_spec(
        [
            TokenRule("tok-comment", _CMT_HASH),
            TokenRule("tok-str", _STR_TDQ),
            TokenRule("tok-str", _STR_DQ),
            TokenRule("tok-tag", r"@[A-Za-z_][A-Za-z0-9_]*"),
            TokenRule("tok-var", r"\$[A-Za-z_][A-Za-z0-9_]*"),
            TokenRule(
                "tok-kw",
                r"\b(?:query|mutation|subscription|fragment|on|type|interface|union|enum|input|"
                r"scalar|extend|schema|directive|implements|repeatable)\b",
            ),
            TokenRule("tok-const", r"\b(?:true|false|null)\b"),
            TokenRule("tok-type", _PASCAL_TYPE),
            TokenRule("tok-num", _NUM_STD),
        ]
    )

    specs["markdown"] = _compile_spec(
        [
            TokenRule("tok-step", r"^[ \t]*#{1,6}[ \t]+[^\n]*"),
            TokenRule("tok-op", r"^[ \t]*(?:`{3,}|~{3,})[^\n]*"),
            TokenRule("tok-str", r"`[^`\n]+`"),
            TokenRule("tok-kw", r"\*\*[^*\n]+\*\*|__[^_\n]+__"),
            TokenRule("tok-comment", r"^[ \t]*>[^\n]*"),
            TokenRule("tok-tag", r"\[[^\]]+\]\([^)]+\)"),
            TokenRule("tok-op", r"^[ \t]*(?:[-*+]|\d+\.)(?=[ \t])"),
        ]
    )

    return specs


_SPECS: Dict[str, LanguageSpec] = _build_specs()

LANGUAGE_ALIASES: Dict[str, str] = {
    # Gherkin / BDD
    "gherkin": "gherkin",
    "feature": "gherkin",
    "cucumber": "gherkin",
    "bdd": "gherkin",
    # Diff
    "diff": "diff",
    "patch": "diff",
    # Groovy / JVM / Katalon / CI
    "groovy": "groovy",
    "gradle": "groovy",
    "jenkinsfile": "groovy",
    "katalon": "groovy",
    "gvy": "groovy",
    "java": "java",
    "kotlin": "kotlin",
    "kt": "kotlin",
    "kts": "kotlin",
    # .NET / Systems / Web Backend
    "csharp": "csharp",
    "cs": "csharp",
    "c#": "csharp",
    "dotnet": "csharp",
    "javascript": "javascript",
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "tsx": "typescript",
    "python": "python",
    "py": "python",
    "python3": "python",
    "py3": "python",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "rs": "rust",
    "cpp": "cpp",
    "c++": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "c": "cpp",
    "h": "cpp",
    "hpp": "cpp",
    "php": "php",
    "ruby": "ruby",
    "rb": "ruby",
    # Shell / CLI
    "powershell": "powershell",
    "ps1": "powershell",
    "pwsh": "powershell",
    "ps": "powershell",
    "psm1": "powershell",
    "bash": "bash",
    "sh": "bash",
    "zsh": "bash",
    "shell": "bash",
    "console": "bash",
    "terminal": "bash",
    "bat": "bat",
    "cmd": "bat",
    "batch": "bat",
    "dos": "bat",
    # Data / Config / Markup / DevOps
    "json": "json",
    "jsonc": "json",
    "jsonl": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "toml",
    "ini": "ini",
    "properties": "ini",
    "conf": "ini",
    "cfg": "ini",
    "env": "ini",
    "dotenv": "ini",
    "sql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "mysql": "sql",
    "sqlite": "sql",
    "tsql": "sql",
    "plsql": "sql",
    "html": "html",
    "htm": "html",
    "xhtml": "html",
    "svg": "html",
    "xml": "html",
    "pom": "html",
    "csproj": "html",
    "plist": "html",
    "xsl": "html",
    "xsd": "html",
    "css": "css",
    "scss": "css",
    "sass": "css",
    "less": "css",
    "dockerfile": "dockerfile",
    "docker": "dockerfile",
    "http": "http",
    "rest": "http",
    "graphql": "graphql",
    "gql": "graphql",
    "markdown": "markdown",
    "md": "markdown",
}

SUPPORTED_LANGUAGES: FrozenSet[str] = frozenset(
    set(_SPECS.keys()) | {"gherkin", "diff"}
)


def resolve_language(lang: str) -> str:
    """
    Normalizes a Markdown fence info-string (e.g. `py`, `python title="app.py"`,
    `.groovy`, `feature`) into a canonical language identifier or `""`.
    """
    if not lang:
        return ""
    head = lang.strip().split()[0].lower().lstrip(".")
    head = re.split(r"[\{,;]", head, maxsplit=1)[0]
    return LANGUAGE_ALIASES.get(head, "")


def highlight_code(code_raw: str, lang: str) -> str:
    """
    Applies zero-bloatware lexical syntax highlighting to a raw code block string.
    Always escapes HTML safely and ensures spans never cross newline boundaries.
    """
    if not code_raw:
        return ""
    canonical = resolve_language(lang)
    if not canonical:
        return _escape(code_raw)
    if canonical == "diff":
        return _highlight_diff(code_raw)
    if canonical == "gherkin":
        return _highlight_gherkin(code_raw)
    spec = _SPECS.get(canonical)
    if spec is None:
        return _escape(code_raw)
    return _highlight_with_spec(code_raw, spec)
