Field-related code reorganized into a ``src/cfx/types/`` sub-package:
``config_field.py`` (``ConfigField`` base), ``types.py`` (concrete field
types, ``Alias``, ``Mirror``), and ``typed_field.py`` (``Field``,
``FieldSpec``, ``resolve_field_spec``).  ``types/__init__.py`` re-exports
the full public surface — all existing ``from cfx import ...`` imports are
unaffected.  Shared dotpath utilities (``walk``, ``walk_set``,
``strip_none``) extracted into ``src/cfx/utils.py``.  ``Alias`` and
``Mirror`` moved from ``views.py`` into ``types/types.py`` alongside the
other field descriptor classes.  ``src/cfx/__init__.py`` rewritten with
explicit re-exports; no bare wildcard imports.
