Custom Fields
=============

When the built-in types don't fit your domain — non-linear ranges, custom unit
normalization, domain-specific enums — extend :class:`~cfx.ConfigField`
directly.  This capability is intentionally preserved alongside
annotation-native syntax: not every field can be expressed via annotations
alone.


Defining your own field
-----------------------

Import the base class from ``cfx.types``::

    from cfx import Config, Field
    from cfx.types import ConfigField

    class Angle(ConfigField):
        """An angle in degrees, stored normalized to [0, 360)."""

        def validate(self, value):
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Angle requires a number, got {type(value).__name__!r}"
                )

        def __set__(self, obj, value):
            if self.static:
                raise AttributeError("Cannot set a static config field.")
            self.validate(value)
            setattr(obj, self.private_name, float(value) % 360.0)


    class SurveyConfig(Config):
        heading = Angle(0.0, "Survey heading in degrees")
        bearing = Angle(45.0, "Bearing to target in degrees")
        radius: float = Field(10.0, "Search radius in meters", minval=0.0)

    cfg = SurveyConfig()
    cfg.heading = 370.0
    cfg.heading             # 10.0  - normalized to [0, 360)
    cfg.heading = -30.0
    cfg.heading             # 330.0 - wrapped around

Explicit field types and ``Field()``-declared fields can coexist freely on
the same class.


Normalizing defaultval
----------------------

When a custom ``__set__`` transforms values (e.g. ``Angle`` wraps degrees to
``[0, 360)``), the transformation runs on every instance assignment but
**not** on the raw ``default_value`` passed to ``ConfigField.__init__``.
``Config.__init__`` seeds each field via ``setattr``, so instances do see the
normalized value.  The descriptor's own ``defaultval`` attribute holds the
original raw value.

This is only a problem if code inspects ``defaultval`` directly (e.g. for
equality tests or documentation generation).  To keep things consistent,
normalize in ``Angle.__init__`` as well::

    class Angle(ConfigField):
        """An angle in degrees, stored normalized to [0, 360)."""

        def __init__(self, default_value, doc, **kwargs):
            if isinstance(default_value, (int, float)):
                default_value = float(default_value) % 360.0
            super().__init__(default_value, doc, **kwargs)

        def validate(self, value):
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Angle requires a number, got {type(value).__name__!r}"
                )

        def __set__(self, obj, value):
            if self.static:
                raise AttributeError("Cannot set a static config field.")
            self.validate(value)
            setattr(obj, self.private_name, float(value) % 360.0)


    class SurveyConfig(Config):
        heading = Angle(370.0, "Survey heading in degrees")

    SurveyConfig().heading                       # 10.0
    type(SurveyConfig()).heading.defaultval      # 10.0 - also normalized


How ``__set__`` and ``validate`` interact
-----------------------------------------

The base :meth:`ConfigField.__set__` does three things in order:

1. Checks ``self.static`` and raises ``AttributeError`` if set.
2. Calls ``self.validate(value)`` to check the raw input.
3. Stores the value directly in ``instance.__dict__`` under the private name.

When you override ``__set__`` to normalize a value, you take over the full
storage path.  The recommended pattern is:

1. Guard ``self.static`` yourself - ``super().__set__()`` is no longer called
   so its guard is bypassed.
2. Call ``self.validate(value)`` on the *raw* input before normalizing.
3. Store the *normalized* value via ``setattr(obj, self.private_name, normalized)``.

This avoids double-validation (validate once on raw, store normalized) and
keeps the check and the store close together.  :class:`~cfx.Path` follows
the same pattern - it coerces strings to ``pathlib.Path`` before storing::

    class Angle(ConfigField):
        def __set__(self, obj, value):
            if self.static:                                       # 1. static guard
                raise AttributeError("Cannot set a static config field.")
            self.validate(value)                                  # 2. validate raw
            setattr(obj, self.private_name, float(value) % 360.0)  # 3. store normalized

.. important::

   Any ``__set__`` override that bypasses ``super().__set__()`` **must**
   re-check ``self.static`` itself.  Forgetting this makes the static flag
   silently ineffective for that field type.
