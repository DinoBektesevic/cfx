``Field()``: annotation-native field factory.  Declare fields with a type
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
