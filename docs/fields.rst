Fields
======

Configs are build out of fields. Fields broadly can be categorized into three
groups: based on declaration style, based on modifiers and as field views.

cfx recognizes three **declaration styles** for fields:

- **Inferred** - the field type is inferred from the type-annotation:
  ``field: int = Field(100, "a field)")``
- **Explicit** - a concrete type ``cfx.types`` is used directly:
  ``threshold = Float(0.5, "a field")``
- **Custom** - user provided implementation of  :class:`~cfx.ConfigField`:
  See :doc:`custom-fields`.

There is nothing special separating these three types. Inferred fields resolve to
a built-in explicit type via annotation lookup and the explicit types are themselves
:class:`~cfx.ConfigField` implementations. Explicit and custom fields exist for
situations when the built-in set doesn't cover your domain. CFX attempts to cover
all broadly used cases, but it is out of scope to provide every possible combination
of unit normalization, value validation, non-standard type coercion and
domain-specific enumerations possible. Implementing this custom functionality is
unfortunately not possible on to do directly on inferred fields.

Based on **modifiers**, cfx recognizes three different types of fields:

* **computed fields**,
* **static fields** and
* **environment** variable backed fields.

See :doc:`field-modifiers` for more details, but in short the key differences
are that:

* computed fields hold a function reference, or a lambda function,  and compute
  their value on access
* static fields are set as constants and are not allowed to be mutated
* environment backed fields derive their value dynamically by reading the value
  of the associated environment variable.

And finally, cfx at the moment recognizes two field views:

* :class:`~cfx.Alias` and
* :class:`~cfx.Mirror`.

These fields look and act like fields but they reference or synchronize *other*
fields within the same or from a different config object rather than storing
values of their own.  See :doc:`views` for more details.


Inferred fields
---------------

The recommended way to declare config fields is with a type annotation and
:func:`~cfx.Field`::

    from cfx import Config, Field
    from typing import Literal

    class ProcessingConfig(Config):
        confid = "processing"
        iterations: int = Field(100, "Number of iterations", minval=1)
        threshold: float = Field(0.5, "Acceptance threshold", minval=0.0, maxval=1.0)
        label: str = Field("run_01", "Human-readable run label")
        mode: Literal["fast", "balanced", "thorough"] = Field("fast", "Processing mode")
        verbose: bool = Field(False, "Enable verbose logging")

The concrete field type is inferred from the annotation at class-definition
time.  Any constraint keyword accepted by the underlying type can be passed
directly to ``Field()`` (e.g. ``minval=``, ``maxval=``, ``env=``,
``static=``).

Mapping to field types
^^^^^^^^^^^^^^^^^^^^^^

At definition time, the type annotation is parsed, alongside any required validation
data, and, under the hood, this lookup mapping is used to construct the matching
explicit field type.

+---------------------------------------+---------------------------+------------------------------------------+
| Annotation                            | Resolved type             | Notes                                    |
+=======================================+===========================+==========================================+
| ``bool``                              | :class:`~cfx.Bool`        |                                          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``int``                               | :class:`~cfx.Int`         | Optional ``minval``, ``maxval``          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``float``                             | :class:`~cfx.Float`       | Optional ``minval``, ``maxval``; also    |
|                                       |                           | accepts ``int``                          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``str``                               | :class:`~cfx.String`      | Optional ``minsize``, ``maxsize``,       |
|                                       |                           | ``predicate``                            |
+---------------------------------------+---------------------------+------------------------------------------+
| ``pathlib.Path``                      | :class:`~cfx.Path`        | Optional ``must_exist=True``             |
+---------------------------------------+---------------------------+------------------------------------------+
| ``Literal["a", "b"]``                 | :class:`~cfx.Options`     | Default must be one of the literals      |
+---------------------------------------+---------------------------+------------------------------------------+
| ``set[Literal["a", "b"]]``            | :class:`~cfx.MultiOptions`|                                          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``list[T]``                           | :class:`~cfx.List`        | Optional ``element_type``, ``minlen``,   |
|                                       |                           | ``maxlen``                               |
+---------------------------------------+---------------------------+------------------------------------------+
| ``tuple[T, T]``                       | :class:`~cfx.Range`       | Validates ``min < max``                  |
+---------------------------------------+---------------------------+------------------------------------------+
| ``int | None``                        | :class:`~cfx.Seed`        | ``None`` means "choose randomly at       |
| ``Optional[int]``                     |                           | runtime"                                 |
+---------------------------------------+---------------------------+------------------------------------------+
| ``int | float``                       | :class:`~cfx.Scalar`      |                                          |
| ``Union[int, float]``                 |                           |                                          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``datetime.date``                     | :class:`~cfx.Date`        |                                          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``datetime.time``                     | :class:`~cfx.Time`        |                                          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``datetime.datetime``                 | :class:`~cfx.DateTime`    | Rejects bare ``date`` instances          |
+---------------------------------------+---------------------------+------------------------------------------+
| ``dict``                              | :class:`~cfx.Dict`        | Untyped free-form dict                   |
+---------------------------------------+---------------------------+------------------------------------------+
| ``typing.Any``                        | :class:`~cfx.Any`         | No validation; signals intentional       |
|                                       |                           | opt-out                                  |
+---------------------------------------+---------------------------+------------------------------------------+
| ``Final[T]``                          | Same as ``T``, static=True| Cannot be set on instances               |
+---------------------------------------+---------------------------+------------------------------------------+


.. _explicit-field-types:

Explicit field types
--------------------

When annotation inference is not enough — custom validation logic,
domain-specific coercion, or constraint combinations not expressible via
annotations — import and use the concrete field classes directly::

    from cfx import Config
    from cfx.types import Float, Options, String

    class ProcessingConfig(Config):
        threshold = Float(0.5, "Acceptance threshold", minval=0.0, maxval=1.0)
        mode = Options(("fast", "balanced"), "Processing mode")
        label = String("run_01", "Human-readable run label", maxsize=64)

.. note::

   :class:`~cfx.Options` and :class:`~cfx.MultiOptions` have a different
   constructor order: ``(options, doc, default_value=None, ...)`` — the
   allowed choices come first.  When using ``Field()`` this is handled
   automatically.

+------------------------------+------------------------------------------------------------------------+
| Type                         | Description                                                            |
+==============================+========================================================================+
| :class:`~cfx.ConfigField`    | Base class. No validation; accepts any value. Use when you intend to   |
|                              | subclass it (see :doc:`custom-fields`).                                |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Any`            | Explicit escape hatch. No validation; signals to readers that the      |
|                              | absence of constraints is intentional.                                 |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Bool`           | ``True`` or ``False``. Rejects ``int`` — unlike Python's own           |
|                              | truthiness, ``1`` is not a ``bool`` here.                              |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Int`            | Integer. Optional ``minval`` and ``maxval``.                           |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Float`          | Float. Also accepts ``int`` on assignment. Optional ``minval`` and     |
|                              | ``maxval``.                                                            |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Scalar`         | Either ``int`` or ``float``. Use when both are acceptable. Optional    |
|                              | ``minval`` and ``maxval``.                                             |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.String`         | Text string. Optional ``minsize``, ``maxsize``, and ``predicate`` (a   |
|                              | callable that returns ``True`` for valid values).                      |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Options`        | One value from a fixed set. Default is the first option unless         |
|                              | ``default_value`` is supplied.                                         |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.MultiOptions`   | A ``set`` that is a subset of a fixed set of choices.                  |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Path`           | A ``pathlib.Path``. Coerces plain strings on assignment. Optional      |
|                              | ``must_exist=True`` to reject paths that do not exist on disk.         |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Seed`           | An ``int`` or ``None``. ``None`` conventionally means "draw randomly   |
|                              | at runtime".                                                           |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Range`          | A ``(min, max)`` tuple. Validates ``min < max``.                       |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.List`           | A list. Optional ``element_type``, ``minlen``, and ``maxlen``.         |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Dict`           | An untyped dict. Useful for free-form sub-structure that is too loose  |
|                              | to warrant a nested :class:`~cfx.Config`.                              |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Date`           | A ``datetime.date``.                                                   |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.Time`           | A ``datetime.time``.                                                   |
+------------------------------+------------------------------------------------------------------------+
| :class:`~cfx.DateTime`       | A ``datetime.datetime``. Rejects bare ``date`` instances.              |
+------------------------------+------------------------------------------------------------------------+
