"""Shared utility functions with no cfx imports."""

# Sentinel for "this CLI argument was not supplied by the user."
# Using None is wrong because some fields (Seed, Any) legitimately accept None
# as a value. _CLI_UNSET lets _apply_params distinguish "not provided" from
# "explicitly provided as None".
_CLI_UNSET = object()


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
