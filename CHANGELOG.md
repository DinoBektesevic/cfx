# cfx 0.7.0 (2026-04-23)

## Features

- Added `is_set()`, `unset()`, and `reset()` public API to `ConfigField`. `is_set(obj)` returns `True` when the field has an explicit value stored on the instance (as opposed to using its callable default or env-var fallback). `unset(obj)` removes the stored value, reverting to the default. `reset(obj, value=None)` either unsets or sets a new value through the full normalize→validate pipeline.
- Added `normalize()` / `validate()` separation to `ConfigField`. `normalize()` runs first (idempotent coercion to canonical form) and `validate()` runs after. Built-in types that previously coerced in `__set__` or `__init__` now implement `normalize()`: `MultiOptions` (list/tuple → set), `Path` (str → `pathlib.Path`), `Range` (list → tuple), `List` (tuple → list), `Date`/`Time`/`DateTime` (ISO string → datetime object).
- Added field-owned CLI: `to_argparse_kwargs()` and `to_click_option()` methods on `ConfigField` replace the monolithic dispatch tables in `cli.py`. Each field type owns its argparse/click representation. `Bool` uses `BooleanOptionalAction` and click flag pairs; `Options` adds `choices`; `MultiOptions` uses `nargs="+"` and `multiple=True`; `Seed`, `Range`, `Path`, `Dict`, `Date`, `Time`, `DateTime` each supply an appropriate `metavar`.
- Added field-owned serialization: `serialize()` and `deserialize()` methods on `ConfigField` replace the monolithic `Config._serialize_value()`. Each field type encodes its own on-disk form. `Path` serializes as a string, `MultiOptions` as a sorted list, `Range` as a list, `Date`/`Time`/`DateTime` as ISO strings. The base implementation is an identity pass-through.
- Added runnable examples (`examples/`), rewrote `custom-fields` docs around the `normalize`/`validate` pattern, added `is_set`/`unset`/`reset` and `validate`-after-`update` sections to the using guide, fixed sharp-edges page, removed TOML references throughout, and wired up `--doctest-modules` so all inline doctests run as part of the test suite.
- Rewrote fields and field-modifiers intro sections for clarity: tradeoff-oriented framing for declaration styles and modifiers, fixed all broken RST cross-references, added `transient=` modifier documentation, moved modifier rough-edges content from fields.rst to field-modifiers.rst where it belongs. Also fixed remaining TOML references in cli.rst, capitalised normalize/validate section heading in custom-fields.rst, added idempotency link to sharp-edges, clarified that `validate()` is on the Config class in advanced.rst, and wired doctest runs into CI.

## Bug Fixes

- Fixed `Config.validate()` not being called after `Config.update()`. Cross-field invariants defined in `validate()` are now enforced on programmatic updates, not only on deserialization.
- Fixed a bug where using `components=` on a subclass silently discarded all fields inherited from the parent class. A `Config` subclass that both inherits from a parent and declares `components=[...]` now correctly includes all inherited fields alongside the new nested sub-configs.
- Path fields now serialize using forward slashes on all platforms. Previously, `str(pathlib.Path(...))` produced backslashes on Windows, breaking cross-platform round-trips when a config was saved on Windows and loaded on Linux or macOS.

## Removals

- Removed TOML serialization support (`from_toml()`, `to_toml()`, and the `toml` optional dependency). TOML cannot represent `None` natively, causing silent data loss for `Seed(None)` and similar fields on round-trip. Use YAML for serialization instead.


# cfx 0.6.0 (2026-04-21)

## Features

- Schema versioning: declare ``_version = <int>`` on a ``Config`` class to
  embed the schema version in ``to_dict()`` output.  ``from_dict()`` emits a
  ``UserWarning`` when the stored version differs from the class version, and
  ignores the ``_version`` key during field assignment (including under
  ``strict=True``).
- ``Field()``: annotation-native field factory.  Declare fields with a type
  annotation and ``Field()`` as the right-hand side — the concrete
  ``ConfigField`` subclass is inferred at class-definition time::

      from cfx import Config, Field
      from typing import Literal

      class SearchConfig(Config):
          n_sigma: float = Field(5.0, "Detection threshold", minval=0.0)
          method: Literal["DBSCAN", "RANSAC"] = Field("DBSCAN", "Algorithm")
          verbose: bool = Field(False, "Enable verbose output")

  Supported annotations: ``bool``, ``int``, ``float``, ``str``,
  ``pathlib.Path``, ``Literal[...]`` → ``Options``,
  ``set[Literal[...]]`` → ``MultiOptions``, ``list[T]`` → ``List``,
  ``tuple[T, T]`` → ``Range``, ``int | None`` → ``Seed``,
  ``int | float`` → ``Scalar``, ``datetime.date/time/datetime``,
  ``dict``, ``typing.Any``, ``Final[T]`` (implies ``static=True``).
  Callable defaults and all constraint kwargs (``minval=``, ``env=``,
  ``static=``, ``transient=``, etc.) pass through to the resolved field type.
  Explicit field types remain fully supported and can coexist with ``Field()``
  on the same class.

## Documentation

- ``docs/`` refactored to split out Fields into 7 separate sections. Add `Fields`, `Field Modifiers` and `Custom Field` documents, expand the subsection in `Fields` to cover the type inferred and explicit fields. (https://github.com/DinoBektesevic/cfx/issues/docs_refactor)
- ``docs/fields.rst`` rewritten: ``Field()`` and annotation syntax are the
  primary declaration style, with explicit types documented as an escape hatch
  for custom validation and domain-specific fields.  Annotation → field type
  mapping table added.  ``docs/index.rst``, ``docs/defining.rst``, and
  ``README.md`` updated to use ``Field()`` throughout.

## Internal

- Field-related code reorganized into a ``src/cfx/types/`` sub-package:
  ``config_field.py`` (``ConfigField`` base), ``types.py`` (concrete field
  types, ``Alias``, ``Mirror``), and ``typed_field.py`` (``Field``,
  ``FieldSpec``, ``resolve_field_spec``).  ``types/__init__.py`` re-exports
  the full public surface — all existing ``from cfx import ...`` imports are
  unaffected.  Shared dotpath utilities (``walk``, ``walk_set``,
  ``strip_none``) extracted into ``src/cfx/utils.py``.  ``Alias`` and
  ``Mirror`` moved from ``views.py`` into ``types/types.py`` alongside the
  other field descriptor classes.  ``src/cfx/__init__.py`` rewritten with
  explicit re-exports; no bare wildcard imports.


# cfx 0.5.0 (2026-04-19)

## Features

- `AliasedView`: a self-contained view that auto-generates prefixed `Alias`
  descriptors for every field in each declared component.  Pass
  ``components=[...]`` and optionally ``aliases=[...]`` to override the
  prefix per component (``None`` gives a flat, unprefixed name).  Name
  conflicts raise ``ValueError`` at class-definition time.
- `FlatView`: an ``AliasedView`` with all prefixes set to ``None`` —
  every component field is exposed directly by name.  Raises on conflicts.
- `Mirror`: a config descriptor that keeps two or more dotpaths in sync.
  Declaring `shared = Mirror("a.x", "b.x")` on a `Config` fans writes to
  every path and asserts agreement on read, raising `ValueError` with a
  diff if the paths disagree.  Accepts `FieldRef` objects or plain dotpath
  strings.
- `FieldRef`: accessing a field or component on a `Config` *class* (rather
  than an instance) now returns a `FieldRef` path proxy instead of the raw
  descriptor. `FieldRef` objects chain attribute access to build validated
  dotpath strings and are the preferred input to `Alias` and `Mirror` — pass
  `Alias(SomeConfig.component.field)` instead of `Alias("component.field")`
  to keep paths refactorable via IDE rename and go-to-definition.
- `ComponentRef`: each component slot on a `Config` class now has a
  descriptor installed automatically, so `SomeConfig.component` returns a
  `FieldRef` that can be chained (`SomeConfig.component.field`). Instance
  access is unchanged.

## Internal

- `_ConfigType` metaclass removed. Field collection and component wiring now
  happen in `Config.__init_subclass__`, which runs at class-definition time
  for every subclass. Behaviour is identical; the metaclass was an
  implementation detail.
- `ConfigMeta` renamed to `_ConfigType` to signal that it is not part of the
  public API and will be replaced by `__init_subclass__` in a future release.
- Internal `getattr(cls, field_name)` call sites in `config.py` and
  `display.py` that previously relied on `ConfigField.__get__` returning the
  descriptor on class access have been updated to use `cls._fields[name]`
  directly.

# cfx 0.4.0 (2026-04-19)

## Removals
- `method="unroll"` composition mode removed. Defining a class with
  `method="unroll"` now raises `TypeError` at class-definition time. Use
  nested composition (the default when `components=` is provided) instead.

## Bug Fixes
- `diff()` now recurses into nested sub-configs. Differences in nested fields
  appear with dot-notation keys (e.g. `"search.n_sigma"`). Previously nested
  changes were silently invisible.
- `update()` now accepts nested confid keys: pass a `dict` to update fields
  within a sub-config, or a `Config` instance to replace it. Previously
  passing a nested confid raised `KeyError`.
- `freeze()` now propagates to all nested sub-configs. Previously `freeze()`
  only blocked writes on flat fields of the top-level config.
- `freeze()` now also prevents replacing a nested sub-config via attribute
  assignment (e.g. `cfg.search = other`).
- CLI: `--field none` for `Seed` (and any field whose `from_string` returns
  `None`) now correctly applies `None` as the field value. Previously the
  `None` return from `from_string` was mistaken for "flag not supplied" and
  silently ignored.
- Nested `components=` are now stored in declaration order. Previously the
  internal dict had components in reverse order, causing sub-configs to appear
  in reversed order in `print(cfg)` and iteration.

# cfx 0.3.0 (2026-04-18)

## Features

- Added `transient` keyword to all field types. Callable defaults are now skipped
  during serialization when no explicit value has been stored — the callable
  reconstructs the value naturally on deserialization. Set `transient=False` to
  preserve the old snapshot behaviour instead.
- Config now implements `__iter__`, completing the dict-like protocol. `for key in cfg` works the same as `for key in cfg.keys()`.

## Bug Fixes

- Unroll composition (`method="unroll"`) now raises `ValueError` at class-definition time when two components share a field name. Previously the conflict was silently resolved by ordering. Override a component field by redeclaring it directly on the composing class.

## Removals

- Removed the `UserWarning` that fired when serializing a config with callable defaults. The warning fired even for correct usage and gave no actionable guidance. The correct behaviour (skip transient fields; use `transient=False` for snapshots) is now the default — see the `transient` feature entry.

## Documentation

- Composition docs updated: unroll field resolution order is now documented explicitly (inherited → components left-to-right → own fields), parallel name conflicts across components are called out with an error example, and the "first component wins" wording that described the old silent-override behaviour has been removed.

## Internal

- Migrated CI linting from flake8 to ruff. Added pre-commit hook running ruff format and ruff check.


# cfx 0.2.1 (2026-04-17)

## Bug Fixes

- Composing two components with the same ``confid`` now raises ``ValueError``
  at class-definition time instead of silently dropping the first component.
- ``Int`` and ``Float`` fields now reject ``bool`` values. Previously
  ``True``/``False`` were silently accepted as ``1``/``0`` because ``bool``
  is a subclass of ``int`` in Python. This was inconsistent with ``Bool``,
  which explicitly rejects integers.
- ``Path.validate()`` now raises ``TypeError`` for non-``Path`` values instead
  of silently returning. ``Path.__init__`` also now normalizes string defaults
  to ``pathlib.Path`` at field-definition time, consistent with the pattern
  described for custom fields.
- ``cfg["confid"]`` now returns the nested sub-config object, fixing a broken
  dict-like contract where ``"source" in cfg`` could be ``True`` but
  ``cfg["source"]`` raised ``KeyError``.

## Documentation

- Documentation improvements: added sharp-edges entries for TOML dropping
  ``None`` values and ``List.from_string`` silent JSON fallback; documented
  ``validate()`` call timing; added ``Options``/``MultiOptions`` parameter
  order note; added "which mode to use" guidance to composition page; added
  intro sentences to serialization, using, sharp-edges, and CLI pages; added
  YAML output example and CLI dot-notation mapping table. Landing page title
  and subtitle styling added via ``custom.css``.

## Internal

- Added ``tests/test_display.py`` covering the display module, plus regression
  tests for the four bug fixes and env-var precedence, nested file loading,
  and ``_repr_html_``.


# cfx 0.2.0 (2026-04-17)

## Features

- Improved ``config_tree`` in ``display.py``: replaced ``textwrap.fill``
  with unicode box-drawing characters (``├─``, ``└─``, ``│``). Multiline
  docstrings are now preserved exactly as written rather than reflowed into
  a single paragraph. Nesting depth is indicated by a 4-space continuation
  indent per level. The Config column cap in ``make_table`` was raised from
  15 to 25 characters so that class names are never broken mid-word.
- ``make_table`` and ``as_table`` now accept a ``table_attrs`` keyword argument
  that adds HTML attributes (e.g. ``class``, ``id``) to the generated
  ``<table>`` element, making it straightforward to target the output with
  custom CSS.

## Documentation

- Switched documentation theme from Alabaster to Furo with light and dark
  mode logos, GitHub and PyPI footer icons, and sidebar sections (User Guide,
  API Reference, Development). Updated the canonical example throughout to
  showcase flat fields alongside deep nested sub-configs. Added a Changelog
  page. Removed redundant per-page ``.. contents::`` directives that conflicted
  with Furo's built-in sidebar navigation.


# cfx 0.1.0 (2026-04-17)

## Features

- Every `Config` subclass now exposes `add_arguments` and `from_argparse` for
  argparse, plus `click_options` and `from_click` for click (optional dependency).
  Nested sub-configs use dot-notation flags (e.g. `--search.n-sigma`), including
  arbitrarily deep nesting (e.g. `--middle.inner.x`). An optional config-file
  positional argument is registered automatically — YAML or TOML files are loaded
  first and CLI flags are applied on top.
- Nested container configs can now declare their own flat fields alongside
  sub-configs. Previously, any flat field on a `method="nested"` class was
  silently discarded. Serialization (`to_dict`, `from_dict`, YAML, TOML),
  display (`str`, `repr`, HTML), equality, `__contains__`, and CLI flags all
  handle the mixed case correctly. Expected dict shape:
  `{"top_field": 99.0, "inner": {"x": 1.0}}`.

## Internal

- Added GitHub Actions CI running pytest and flake8 across Python 3.11–3.14 on
  Ubuntu, Windows, and macOS. Added a monthly canary workflow against Python
  pre-releases. Docs are built and hosted automatically by Read the Docs on every
  push to main and on version tags.
- Renamed internal `_from_env_str` to the public `from_string` on all
  `ConfigField` subclasses. Added symmetric `to_string` for display. The display
  table now renders `Path`, `Dict`, `Date`, `Time`, `DateTime`, and `MultiOptions`
  values cleanly instead of using raw `repr`.
- Renamed internal class attribute `defaults` to `_fields` for clarity.
  `_fields` holds flat `ConfigField` descriptors; `_nested_classes` holds
  component classes. The underscore prefix on both makes the symmetry explicit.
- Type coercions moved into `ConfigField.__set__`: `List` coerces tuples to
  lists, `MultiOptions` coerces lists and tuples to sets. This removes ad-hoc
  coercion from `from_argparse` and `from_click` and ensures consistent
  behaviour regardless of how a value is assigned.
