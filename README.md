<p align="center">
  <img src="https://raw.githubusercontent.com/DinoBektesevic/cfx/main/docs/_static/logo/color_large.svg" alt="cfx" width="300">
</p>

<p align="center">
  <a href="https://github.com/DinoBektesevic/cfx/actions/workflows/ci.yml">
    <img src="https://github.com/DinoBektesevic/cfx/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://cfx.readthedocs.io/en/latest/">
    <img src="https://readthedocs.org/projects/cfx/badge/?version=latest" alt="Docs">
  </a>
  <a href="https://pypi.org/project/cfx/">
    <img src="https://img.shields.io/pypi/v/cfx" alt="PyPI">
  </a>
</p>

# cfx

Declare configuration fields next to the classes that use them.
Each field carries its own default value, type checking, and documentation.
Compose flat and nested configs freely — the display shows a unified tree and table.

```python
from cfx import Config, Float, String, Bool

class CalibConfig(Config):
    """Photometric calibration parameters."""
    confid = "calib"
    scale = Float(1.0, "Flux scale factor")
    zero_point = Float(25.0, "Photometric zero-point")

class SourceConfig(Config, components=[CalibConfig]):
    """Source detection and measurement."""
    confid = "source"
    n_sigma = Float(3.0, "Detection threshold in sigma")

class PipelineConfig(Config, components=[SourceConfig]):
    """Image analysis pipeline."""
    confid = "pipeline"
    run_id = String("run_01", "Run identifier")
    dry_run = Bool(False, "Validate only; skip writes")

cfg = PipelineConfig()
print(cfg)
```

```
PipelineConfig: Image analysis pipeline.
└─ SourceConfig: Source detection and measurement.
    └─ CalibConfig: Photometric calibration parameters.
Config         | Key        | Value  | Description
---------------+------------+--------+-----------------------------
PipelineConfig | run_id     | run_01 | Run identifier
PipelineConfig | dry_run    | False  | Validate only; skip writes
SourceConfig   | n_sigma    | 3.0    | Detection threshold in sigma
CalibConfig    | scale      | 1.0    | Flux scale factor
CalibConfig    | zero_point | 25.0   | Photometric zero-point
```

## Installation

```bash
pip install cfx
```

With optional serialization and CLI backends:

```bash
pip install "cfx[yaml]"   # adds PyYAML
pip install "cfx[toml]"   # adds tomli-w
pip install "cfx[click]"  # adds Click
pip install "cfx[all]"    # everything
```

## Quick start

```python
from cfx import Config, Int, Float, String, Options, Bool, Path

class ProcessingConfig(Config):
    confid = "processing"
    iterations = Int(100, "Number of iterations", minval=1)
    threshold = Float(0.5, "Acceptance threshold", minval=0.0, maxval=1.0)
    label = String("run_01", "Human-readable run label")
    mode = Options(("fast", "balanced", "thorough"), "Processing mode")
    verbose = Bool(False, "Enable verbose logging")

cfg = ProcessingConfig()

# Dot access and dict-style access are interchangeable
cfg.iterations = 200
cfg["mode"] = "thorough"

# Bad values raise immediately
cfg.threshold = 1.5   # ValueError: Expected value <= 1.0, got 1.5

# Serialize to dict, YAML, or TOML
d = cfg.to_dict()
cfg2 = ProcessingConfig.from_dict(d)

# Copy with overrides, diff two instances
modified = cfg.copy(iterations=500)
cfg.diff(modified)   # {'iterations': (200, 500)}
```

### Environment variables

Back any field with an environment variable — the value is read lazily, so
the same class works across environments without subclassing:

```python
class ServiceConfig(Config):
    host = String("localhost", "Database host", env="DB_HOST")
    port = Int(5432, "Port", env="DB_PORT")

# DB_HOST=prod.example.com python run.py
cfg = ServiceConfig()
cfg.host   # 'prod.example.com' — from env, no code change needed
```

### CLI

Every config exposes `add_arguments` / `from_argparse` for argparse and
`click_options` / `from_click` for Click. Nested sub-configs use dot-notation
flags automatically:

```python
import argparse

parser = argparse.ArgumentParser()
ProcessingConfig.add_arguments(parser)
cfg = ProcessingConfig.from_argparse(parser.parse_args())
# python run.py --iterations 200 --mode thorough --no-verbose
```

## License

GPL-3.0-only — see [LICENSE](LICENSE).
