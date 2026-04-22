Schema versioning: declare ``_version = <int>`` on a ``Config`` class to
embed the schema version in ``to_dict()`` output.  ``from_dict()`` emits a
``UserWarning`` when the stored version differs from the class version, and
ignores the ``_version`` key during field assignment (including under
``strict=True``).
