"""View classes for projecting Config trees into custom namespaces.

A view binds to one or more `Config` instances and exposes a curated or
auto-generated subset of their fields under new names.  Reads and writes
delegate through to the underlying config — views carry no field data of
their own.

Public API
----------
Alias
    Descriptor that maps a view attribute to a dotpath on the bound config.
ConfigView
    Base class for hand-written curated projections.
"""

from typing import ClassVar

from .refs import FieldRef

__all__ = ["Alias", "ConfigView", "Mirror"]


#############################################################################
# Path-walking helpers
#############################################################################


def _walk(root, path: str):
    """Return the value at *path* starting from *root*."""
    obj = root
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def _walk_set(root, path: str, value):
    """Set *value* at *path* starting from *root*."""
    parts = path.split(".")
    obj = root
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


#############################################################################
# Alias descriptor
#############################################################################


class Alias:
    """A view field that delegates reads and writes to a dotpath on the
    bound config.

    Declare `Alias` attributes on a `ConfigView` subclass to define which
    fields of the underlying config are exposed and under what names.  The
    argument is either a `FieldRef` obtained by class-level attribute access
    on a `Config` class, or a plain dotpath string::

        class CalibSummaryView(ConfigView):
            psf_kernel = Alias(PSFFittingConfig.kernel_estimate)  # preferred
            threshold  = Alias("detection.threshold")              # also works

    Parameters
    ----------
    ref : `FieldRef` or `str`
        Path to the target field on the bound config.  Pass a `FieldRef`
        (from class-level attribute access on a `Config`) to keep the path
        refactorable via IDE rename tools.  A plain dotpath string is
        accepted for convenience.
    """

    def __init__(self, ref):
        self._path = ref._path if isinstance(ref, FieldRef) else ref

    def __set_name__(self, owner, name: str):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return FieldRef(self.name, None)
        return _walk(obj._alias_root, self._path)

    def __set__(self, obj, value):
        _walk_set(obj._alias_root, self._path, value)


#############################################################################
# Mirror descriptor
#############################################################################


class Mirror:
    """A config field that keeps multiple dotpaths in sync.

    Declare a ``Mirror`` on a ``Config`` class to enforce that two or more
    fields always hold the same value.  A write fans out to every path; a
    read asserts all paths agree and returns the shared value::

        class SyncedConfig(Config, components=[CameraConfig, DetectorConfig]):
            gain = Mirror(CameraConfig.gain, DetectorConfig.gain)

    Parameters
    ----------
    *refs : `FieldRef` or `str`
        Dotpaths (relative to the config instance) that must stay in sync.
        Pass `FieldRef` objects obtained from class-level attribute access on
        a ``Config`` for refactorable, IDE-navigable paths.
    """

    def __init__(self, *refs):
        self._paths = [r._path if isinstance(r, FieldRef) else r for r in refs]

    def __set_name__(self, owner, name: str):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return FieldRef(self.name, None)
        values = [_walk(obj, p) for p in self._paths]
        if len(set(values)) > 1:
            raise ValueError(
                f"Mirror {self.name!r} paths disagree: "
                f"{dict(zip(self._paths, values, strict=True))}"
            )
        return values[0]

    def __set__(self, obj, value):
        for p in self._paths:
            _walk_set(obj, p, value)


#############################################################################
# ConfigView
#############################################################################


class ConfigView:
    """Base class for curated projections over a `Config` instance.

    Subclass `ConfigView` and declare `Alias` attributes to expose a
    selected subset of fields from one or more configs under names that
    suit the consumer's context.  All reads and writes delegate to the
    bound config — the view itself holds no values::

        class CalibSummaryView(ConfigView):
            psf_kernel = Alias(PSFFittingConfig.kernel_estimate)
            zero_point = Alias(PhotometryConfig.zero_point)

        view = CalibSummaryView(pipeline.calibration)
        view.psf_kernel           # reads pipeline.calibration.psf_fitting...
        view.psf_kernel = 3.5     # writes through

    Views can span multiple sub-configs by binding to a common parent::

        class PipelineSummaryView(ConfigView):
            psf_kernel = Alias(CalibrationConfig.psf_fitting.kernel_estimate)
            threshold  = Alias(DetectionConfig.threshold)

        view = PipelineSummaryView(pipeline_cfg)

    Parameters
    ----------
    config : `Config`
        The config instance to bind to.  All alias paths are resolved
        relative to this object.
    """

    _aliases: ClassVar[dict[str, Alias]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._aliases = {
            k: v for k, v in vars(cls).items() if isinstance(v, Alias)
        }

    def __init__(self, config):
        self._alias_root = config

    def to_dict(self):
        """Return a plain dict of the aliased fields and their current values.

        Returns
        -------
        d : `dict`
            Mapping of alias name to current value for every declared `Alias`.
        """
        return {
            name: _walk(self._alias_root, a._path)
            for name, a in type(self)._aliases.items()
        }

    @classmethod
    def from_dict(cls, d, config):
        """Bind *config* and apply values from *d* through the view's aliases.

        Parameters
        ----------
        d : `dict`
            Alias names and replacement values.
        config : `Config`
            The config instance to bind and write into.

        Returns
        -------
        view : `ConfigView`
            A bound view with *d* values applied.
        """
        view = cls(config)
        for k, v in d.items():
            if k in cls._aliases:
                _walk_set(config, cls._aliases[k]._path, v)
        return view

    def __repr__(self):
        vals = {
            name: _walk(self._alias_root, a._path)
            for name, a in type(self)._aliases.items()
        }
        return f"{type(self).__name__}({vals!r})"

    @classmethod
    def _repr_html_(cls):
        rows = "".join(
            f"<tr><td><code>{name}</code></td>"
            f"<td><code>{a._path}</code></td></tr>"
            for name, a in cls._aliases.items()
        )
        return (
            f"<table><thead><tr><th>Alias</th><th>Path</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )
