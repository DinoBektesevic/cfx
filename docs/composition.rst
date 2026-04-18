Config composition
==================


.. _composition:

Inheritance
-----------

Standard Python inheritance works naturally.  The metaclass collects fields
from the full MRO, so a child class has all parent fields plus any it adds
or overrides::

    from cfx import Config, Int, Float, Options

    class ProcessingConfig(Config):
        confid = "processing"
        iterations = Int(100, "Number of iterations", minval=1)
        threshold = Float(0.5, "Acceptance threshold", minval=0.0, maxval=1.0)
        mode = Options(("fast", "balanced", "thorough"), "Processing mode")

    class ChildConfig(ProcessingConfig):
        confid = "child"
        mode = Options(("fast", "balanced", "thorough"), "Processing mode",
                       default_value="balanced")  # changed default
        max_size = Int(1000, "Maximum item count", minval=1)

    cfg = ChildConfig()
    cfg.iterations  # 100 — inherited
    cfg.mode        # 'balanced' — default changed by child
    cfg.max_size    # 1000 — new field added by child


Composing with ``components=``
------------------------------

Pass a list of config classes as ``components=`` to assemble them into a
larger config::

    from cfx import String

    class FormatConfig(Config):
        confid = "format"
        precision = Int(6, "Decimal precision")
        encoding = String("utf-8", "Output encoding")

    class PipelineConfig(Config, components=[ProcessingConfig, FormatConfig]):
        pass

    cfg = PipelineConfig()
    cfg.processing.iterations  # 100
    cfg.format.precision       # 6

By default each component becomes a sub-object accessible by its ``confid``.

.. rubric:: The ``confid`` attribute

Every config class has a ``confid`` string identifier.  If you do not set it
explicitly, the metaclass assigns the **lowercase class name** automatically::

    class QuickConfig(Config):
        field1 = Int(1, "A field")

    QuickConfig.confid   # 'quickconfig'

Set ``confid`` explicitly whenever a class will be used as a component, so
the resulting attribute name is predictable::

    class FormatConfig(Config):
        confid = "format"  # accessible as parent_cfg.format
        precision = Int(6, "Decimal precision")

``confid`` becomes the attribute name in nested composition and the key in
nested serialization.


Nested sub-configs
------------------

The default composition mode is ``"nested"``.  Each component becomes a fresh
sub-object on every parent instance, accessible as an attribute named after
its ``confid``::

    cfg = PipelineConfig()
    cfg.processing.iterations = 200
    cfg.format.precision = 3

    print(cfg.processing)   # full table for ProcessingConfig
    print(cfg.format)       # full table for FormatConfig

Each parent instance gets its own independent sub-configs.  Mutating
``cfg1.processing`` has no effect on ``cfg2.processing``.

``to_dict()`` produces a nested dict keyed by confid; ``from_dict()`` routes
each sub-dict back to its component class::

    cfg.to_dict()
    # {'processing': {'iterations': 200, 'threshold': 0.5, ...},
    #  'format': {'precision': 3, 'encoding': 'utf-8'}}

    cfg2 = PipelineConfig.from_dict(cfg.to_dict())


Flat merge (unroll)
-------------------

Pass ``method="unroll"`` to merge fields from all components into one flat
namespace.  When field names clash, the **first component wins**; the
composing class's own fields win over all::

    class RunConfig(Config, components=[ProcessingConfig, FormatConfig], method="unroll"):
        """All fields from ProcessingConfig and FormatConfig at the top level."""
        run_id = Int(0, "Unique run identifier")

    cfg = RunConfig()
    cfg.iterations  # 100 — from ProcessingConfig
    cfg.precision   # 6 — from FormatConfig
    cfg.run_id      # 0 — RunConfig's own field

    print(cfg)  # single table listing every field from all three classes


Which mode to use
-----------------

Use **nested** when sub-systems are logically independent and you want
``cfg.processing`` and ``cfg.format`` to be distinct namespaces.
Use **unroll** when you want a flat namespace and don't need to address
sub-configs by name.

When in doubt, start with nested — it's easier to introspect and serialize.
