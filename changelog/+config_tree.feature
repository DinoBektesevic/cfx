Improved ``config_tree`` in ``display.py``: replaced ``textwrap.fill``
with unicode box-drawing characters (``├─``, ``└─``, ``│``). Multiline
docstrings are now preserved exactly as written rather than reflowed into
a single paragraph. Nesting depth is indicated by a 4-space continuation
indent per level. The Config column cap in ``make_table`` was raised from
15 to 25 characters so that class names are never broken mid-word.
