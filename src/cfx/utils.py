"""Shared utility functions with no cfx imports."""


def walk(root, path: str):
    """Return the value at dotpath *path* starting from *root*."""
    obj = root
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def walk_set(root, path: str, value):
    """Set *value* at dotpath *path* starting from *root*."""
    parts = path.split(".")
    obj = root
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


def strip_none(d: dict) -> dict:
    """Recursively remove keys whose value is None."""
    return {
        k: (strip_none(v) if isinstance(v, dict) else v)
        for k, v in d.items()
        if v is not None
    }
