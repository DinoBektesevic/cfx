"""Formatting helpers for rendering Config instances as text or HTML tables.

This module is intentionally not re-exported from the top-level package.
Import directly when needed::

    from pyconf.display import make_table, wrap_cell

Public API
----------
textwrap_cell, textwrap_row
    Text/terminal table cell and row helpers.
wrap_cell, wrap_row
    HTML tag helpers with optional attribute support.
make_table
    Unified table builder — produces either a fixed-width text table or an
    HTML ``<table>`` from a list of ``(name, value, doc)`` rows.
as_table
    Full config renderer for ``__str__`` (format ``"text"``) and
    ``_repr_html_`` (format ``"html"``).
as_inline_string
    Compact ``ClassName(k=v, ...)`` one-liner for ``__repr__``.
"""

import textwrap

__all__ = [
    "textwrap_cell",
    "textwrap_row",
    "wrap_cell",
    "wrap_row",
    "make_table",
    "as_table",
    "as_inline_string",
]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def textwrap_cell(text, max_w):
    """Wrap *text* to at most *max_w* characters, returning a list of lines.

    An empty string produces a single-element list ``[""]`` so that callers
    never receive an empty list.

    Parameters
    ----------
    text : str
        Cell content to wrap.
    max_w : int
        Maximum line width in characters.

    Returns
    -------
    list of str
    """
    lines = textwrap.wrap(str(text), max_w)
    return lines if lines else [""]


def textwrap_row(row, max_widths):
    """Apply `textwrap_cell` to each of the three columns in *row*.

    Parameters
    ----------
    row : tuple of str
        ``(key, value, description)`` strings.
    max_widths : tuple of int
        ``(max_key_w, max_value_w, max_desc_w)`` column limits.

    Returns
    -------
    list of list of str
        One list-of-lines per column.
    """
    return [textwrap_cell(str(row[i]), max_widths[i]) for i in range(3)]


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def wrap_cell(content, tag="td", attrs=None):
    """Wrap *content* in an HTML tag.

    Parameters
    ----------
    content : str
        Inner HTML content.
    tag : str, optional
        HTML element name. Default ``"td"``.
    attrs : dict or None, optional
        Mapping of attribute name to value appended to the opening tag,
        e.g. ``{"class": "cfg-key", "id": "n_sigma"}``.

    Returns
    -------
    str
        ``<tag [attrs]>content</tag>``.
    """
    attr_str = ""
    if attrs:
        attr_str = " " + " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"<{tag}{attr_str}>{content}</{tag}>"


def wrap_row(cells, tag="tr", attrs=None):
    """Wrap a sequence of cell strings in an HTML row tag.

    Parameters
    ----------
    cells : iterable of str
        Cell HTML strings to concatenate inside the row.
    tag : str, optional
        HTML element name. Default ``"tr"``.
    attrs : dict or None, optional
        Mapping of attribute name to value, e.g. ``{"class": "cfg-row"}``.

    Returns
    -------
    str
        ``<tag [attrs]>cells...</tag>``.
    """
    attr_str = ""
    if attrs:
        attr_str = " " + " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"<{tag}{attr_str}>{''.join(cells)}</{tag}>"


# ---------------------------------------------------------------------------
# Internal helpers  (not in __all__)
# ---------------------------------------------------------------------------

def fmt_text_row(wrapped_cells, widths):
    """Format pre-wrapped cells into a fixed-width ``" | "``-separated row.

    Parameters
    ----------
    wrapped_cells : list of list of str
        One list-of-lines per column, as returned by `textwrap_row`.
    widths : list of int
        Actual column widths (used for left-justifying each line).

    Returns
    -------
    str
        One or more lines joined by ``"\\n"``.
    """
    n = max(len(c) for c in wrapped_cells)
    out = []
    for i in range(n):
        parts = [
            (wrapped_cells[col][i] if i < len(wrapped_cells[col]) else "").ljust(widths[col])
            for col in range(3)
        ]
        out.append(" | ".join(parts))
    return "\n".join(out)


def table_rows(cfg):
    """Extract ``(field_name, current_value, doc)`` tuples from *cfg*.

    Parameters
    ----------
    cfg : Config
        Any `Config` instance.

    Returns
    -------
    list of tuple
    """
    return [(k, getattr(cfg, k), getattr(type(cfg), k).doc) for k in cfg.keys()]


# ---------------------------------------------------------------------------
# Unified table builder
# ---------------------------------------------------------------------------

def make_table(rows, format="text", max_key_width=20, max_value_width=25, max_desc_width=50):
    """Format ``(name, value, doc)`` rows as a text or HTML table.

    Parameters
    ----------
    rows : list of tuple
        Each tuple is ``(key, value, description)``.
    format : {"text", "html"}, optional
        Output format. Default ``"text"``.
    max_key_width, max_value_width, max_desc_width : int, optional
        Column width limits for text mode. Ignored in HTML mode.

    Returns
    -------
    str
        Fixed-width text table or ``<table>…</table>`` HTML string.
    """
    if format == "html":
        header_row = wrap_row([
            wrap_cell("Key",         tag="th"),
            wrap_cell("Value",       tag="th"),
            wrap_cell("Description", tag="th"),
        ])
        body = "".join(
            wrap_row([
                wrap_cell(f"<code>{k}</code>"),
                wrap_cell(f"<code>{v!r}</code>"),
                wrap_cell(d),
            ])
            for k, v, d in rows
        )
        return f"<table>{header_row}{body}</table>"

    # text mode
    header = ("Key", "Value", "Description")
    max_widths = (max_key_width, max_value_width, max_desc_width)
    wrapped_header = textwrap_row(header, max_widths)
    wrapped_rows = [textwrap_row(r, max_widths) for r in rows]
    all_wrapped = [wrapped_header] + wrapped_rows
    widths = [
        max(len(line) for wr in all_wrapped for line in wr[i])
        for i in range(3)
    ]
    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt_text_row(wrapped_header, widths), sep] + [
        fmt_text_row(wr, widths) for wr in wrapped_rows
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Config renderers
# ---------------------------------------------------------------------------

def as_table(cfg, format="text"):
    """Render a `Config` instance as a full text or HTML table.

    Handles both flat configs (fields rendered as rows) and nested configs
    (sub-configs rendered recursively).

    Parameters
    ----------
    cfg : Config
        The config instance to render.
    format : {"text", "html"}, optional
        Output format. Default ``"text"``.

    Returns
    -------
    str
        Complete rendered representation including title and docstring.
    """
    nested_classes = getattr(type(cfg), "_nested_classes", {})
    title = type(cfg).__name__
    doc = type(cfg).__doc__

    if format == "html":
        doc_html = f"<p>{doc.strip()}</p>" if doc else ""
        if nested_classes:
            sub_html = "".join(
                as_table(getattr(cfg, confid), format="html")
                for confid in nested_classes
            )
            return f"<b>{title}</b>{doc_html}{sub_html}"
        return f"<b>{title}</b>{doc_html}" + make_table(table_rows(cfg), format="html")

    # text mode
    header = f"{title}:"
    if doc:
        header += f"\n{doc.strip()}"
    if nested_classes:
        sub_tables = "\n\n".join(
            f"[{confid}]\n{as_table(getattr(cfg, confid), format='text')}"
            for confid in nested_classes
        )
        return header + "\n" + sub_tables
    return header + "\n" + make_table(table_rows(cfg), format="text")


def as_inline_string(cfg):
    """Render a `Config` instance as a compact ``ClassName(k=v, ...)`` string.

    Parameters
    ----------
    cfg : Config
        The config instance to render.

    Returns
    -------
    str
        Single-line representation suitable for ``__repr__``.
    """
    nested_classes = getattr(type(cfg), "_nested_classes", {})
    if nested_classes:
        pairs = ", ".join(
            f"{confid}={as_inline_string(getattr(cfg, confid))}"
            for confid in nested_classes
        )
    else:
        pairs = ", ".join(f"{k}={getattr(cfg, k)!r}" for k in cfg.keys())
    return f"{type(cfg).__name__}({pairs})"
