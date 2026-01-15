# High-Level Builder API

## Overview

This document introduces a high-level builder for PyUPPAAL that lets you construct
templates and edges without manually specifying `location_id` or `location_pos`.
The builder generates globally unique IDs and valid positions for you, then
creates standard `Template`, `Location`, and `Edge` objects compatible with the
existing importer/exporter.

The low-level API remains strict: IDs are globally unique and positions are required.
The builder just hides those requirements behind a simpler interface.

---

## When to Use

Use the builder if you want to:
- write short, readable Python model definitions,
- avoid precomputing coordinates,
- avoid manual ID management,
- keep full compatibility with `UModel.from_components()` and PyExporter.

---

## Quick Start

```python
from pyuppaal.simple_builder import ModelBuilder

mb = ModelBuilder()
t = mb.template("Proc")
t.location("Start", initial=True)
t.location("End")
t.edge("Start", "End", guard="x < 5")

templates = mb.build_templates()
```

---

## Public API

### `ModelBuilder`

Constructor:
```python
ModelBuilder(
    *,
    start_id: int = 1,
    id_strategy: str = "sequential",
    pos_strategy: str = "grid",
    grid_step: tuple[int, int] = (200, 150),
    row_len: int = 6,
    template_offset: tuple[int, int] = (1200, 0),
    origin: tuple[int, int] = (0, 0),
)
```

Key methods:
```python
template(name: str, *, params: str | None = None, declaration: str | None = None) -> TemplateBuilder
build_templates() -> list[Template]
build_umodel(
    *,
    declaration: str = "",
    system: str = "",
    queries: list[str] | None = None,
    model_path: str | None = None
) -> UModel
```

Notes:
- `start_id` is useful when adding templates to an existing model:
  `start_id = existing_model.max_location_id + 1`.
- `id_strategy` and `pos_strategy` are currently fixed to `"sequential"` and `"grid"`
  but remain configurable for future extensions.

### `TemplateBuilder`

```python
location(
    name: str,
    *,
    initial: bool = False,
    urgent: bool = False,
    committed: bool = False,
    branchpoint: bool = False,
    pos: tuple[int, int] | None = None,
    invariant: str | None = None,
    rate_of_exponential: float | None = None,
    comments: str | None = None,
    test_code_on_enter: str | None = None,
    test_code_on_exit: str | None = None,
) -> str

edge(
    source: str,
    target: str,
    *,
    select: str | None = None,
    sync: str | None = None,
    update: str | None = None,
    guard: str | None = None,
    probability_weight: float | None = None,
    comments: str | None = None,
    test_code: str | None = None,
    nails: list[tuple[int, int]] | None = None,
    source_pos: tuple[int, int] | None = None,
    target_pos: tuple[int, int] | None = None,
) -> None

set_initial(name: str) -> None
to_template() -> Template
```

Rules:
- Location names must be unique within a template.
- Exactly one initial location is required per template.
- `edge()` uses location names and resolves IDs internally.

---

## Internal Strategies (Not Public API)

The builder uses private strategy objects to generate IDs and positions. These
are internal to `simple_builder.py` and are not exported:

```
class _IdAllocator:
    def next_id(self) -> int: ...

class _PosPlacer:
    def pos_for(..., explicit_pos: tuple[int, int] | None) -> tuple[int, int]: ...
```

Default implementations:
- `_SequentialIdAllocator`: global sequential IDs owned by `ModelBuilder`
- `_GridPosPlacer`: deterministic grid layout per template

This makes the internals replaceable without changing the public API.

---

## Default Layout Behavior

If you do not pass `pos` to `location()`, positions are generated using a grid:

- each template gets a base offset,
- locations fill left-to-right, then wrap to the next row,
- spacing is controlled by `grid_step` and `row_len`.

This guarantees valid coordinates without requiring manual geometry.

---

## Using with `UModel.from_components`

```python
from pyuppaal.simple_builder import ModelBuilder

mb = ModelBuilder(start_id=1)
t = mb.template("Proc")
t.location("Start", initial=True)
t.location("End")
t.edge("Start", "End")

model = mb.build_umodel(
    declaration="clock x;",
    system="system Proc;",
    queries=["A[] not deadlock"],
)
```

---

## Using in Human-Mode Export (registry.py)

```python
from pyuppaal.simple_builder import ModelBuilder

mb = ModelBuilder()
t = mb.template("Proc")
t.location("Start", initial=True)
t.location("End")
t.edge("Start", "End", guard="x < 5")

ALL_TEMPLATES = mb.build_templates()

def load_global_declaration():
    return "clock x;"

def load_system_declaration():
    return "system Proc;"

def load_queries():
    return ["A[] not deadlock"]
```

---

## Compatibility Notes

The builder produces standard `Template`, `Location`, and `Edge` objects. That means:
- PyExporter can export them directly.
- PyImporter can import them back to `UModel`.
- Validation rules remain unchanged (global unique IDs and required positions).
