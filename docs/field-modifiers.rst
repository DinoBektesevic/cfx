Field Modifiers
===============

Field modifiers are keyword arguments that change how a field stores or
resolves its value.  They apply to any field regardless of declaration style —
inferred, explicit, or custom (see :doc:`fields`).


Computed fields
---------------

Any field supports a **callable** default — a function that receives the
live config instance and is evaluated on every read where no explicit value
has been stored::

    class DetectionConfig(Config):
        stddev: float = Field(1.0, "Measured standard deviation")
        sigma3: float = Field(lambda self: self.stddev * 3, "3-sigma threshold")
        sigma5: float = Field(lambda self: self.stddev * 5, "5-sigma threshold")

    cfg = DetectionConfig()
    cfg.stddev = 2.0
    cfg.sigma3   # 6.0
    cfg.sigma5   # 10.0

    cfg.sigma5 = 99.0   # store an explicit override
    cfg.sigma5          # 99.0 - stored value; formula no longer called

Callable defaults are skipped during serialization when no explicit value
has been stored — they reconstruct from the class definition on load.
See :ref:`sharp-edges-serialization` for edge cases.


Static fields
-------------

Set ``static=True`` (or annotate with ``Final[T]``) to make a field a
class-level constant.  Static fields are readable on instances but raise
``AttributeError`` on assignment::

    from typing import Final

    class RunConfig(Config):
        schema_rev: Final[int] = Field(2, "Config schema revision")
        timeout: float = Field(30.0, "Request timeout in seconds")

    cfg = RunConfig()
    cfg.schema_rev        # 2
    cfg.schema_rev = 3    # AttributeError: Cannot set a static config field.

Both forms are equivalent::

    # annotation form
    schema_rev: Final[int] = Field(2, "Config schema revision")

    # explicit kwarg form — also works with explicit types (see :doc:`fields`)
    schema_rev = Int(2, "Config schema revision", static=True)


Environment variables
---------------------

Pass ``env=`` to back any field with an environment variable.  The variable
is read lazily, so the same class works across environments without
subclassing::

    import os
    from cfx import Config, Field

    class DatabaseConfig(Config):
        host: str = Field("localhost", "Database host", env="DB_HOST")
        port: int = Field(5432, "Database port", env="DB_PORT")

    os.environ["DB_HOST"] = "db.example.com"
    cfg = DatabaseConfig()
    cfg.host    # 'db.example.com' - from env var
    cfg.port    # 5432 - env var not set; falls back to default

The lookup priority on every field read is:

1. An explicit value stored on the instance (via assignment or
   :meth:`~cfx.Config.from_dict`).
2. The environment variable named by ``env``, if the variable is present in
   ``os.environ``.
3. The ``default_value`` passed to the field constructor (called if callable).

Once an explicit value is stored, the environment variable is no longer
consulted::

    cfg.host = "override.example.com"
    os.environ["DB_HOST"] = "ignored"
    cfg.host    # 'override.example.com'
