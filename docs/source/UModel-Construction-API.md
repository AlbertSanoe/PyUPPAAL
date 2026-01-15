# UModel Construction API

## Overview

This document describes the refactored UModel construction mechanism in PyUPPAAL. The refactoring introduces a unified internal initialization system that ensures consistency across all construction paths while eliminating side effects during model loading.

### Key Improvements

1. **Unified Initialization**: All construction paths now use a single internal method `_init_from_components()`.
2. **Pure XML Parsing**: The new `_parse_xml()` method reads XML files without side effects (no automatic file modification).
3. **Consistent Behavior**: Both XML-based and component-based construction follow the same initialization logic.
4. **Predictable Queries**: The `queries` property now always returns `List[str]`, never `None`.

---

## Construction Paths

UModel supports two primary construction paths:

### 1. XML-Based Construction

Load an existing UPPAAL XML model file:

```python
from pyuppaal import UModel

# Load from existing XML file
model = UModel("path/to/model.xml")
```

**Internal Flow:**
1. `__init__()` validates the file path
2. `_parse_xml()` parses the XML file (read-only, no side effects)
3. `_init_from_components()` initializes the instance with parsed components
4. Autosave is enabled by default

### 2. Component-Based Construction

Create a model programmatically from components:

```python
from pyuppaal import UModel
from pyuppaal.nta import Template, Location, Edge

# Define components
declaration = "clock x;"
templates = [template1, template2]  # List of Template objects
system = "system Process1, Process2;"
queries = ["A[] not deadlock", "E<> Process1.goal"]

# Create model from components
model = UModel.from_components(
    declaration=declaration,
    templates=templates,
    system=system,
    queries=queries
)
```

**Internal Flow:**
1. `from_components()` normalizes inputs (e.g., `queries=None` becomes `[]`)
2. Creates instance using `object.__new__()` to bypass `__init__()`
3. `_init_from_components()` initializes the instance
4. Autosave is disabled by default (no file path required)

---

## Internal APIs

### `_init_from_components()`

**Purpose**: Unified internal initialization method used by all construction paths.

**Signature:**
```python
def _init_from_components(
    self,
    declaration: str,
    templates: List[Template],
    system: str,
    queries: List[str],
    model_path: str | None,
    autosave: bool
) -> None
```

**Parameters:**
- `declaration` (str): Global declarations string
- `templates` (List[Template]): List of Template objects
- `system` (str): System declaration string
- `queries` (List[str]): Query strings list (never `None`, use `[]` for empty)
- `model_path` (str | None): Model file path (can be `None` for in-memory models)
- `autosave` (bool): Whether to enable automatic saving on property changes

**Behavior:**
- Sets all private attributes using name mangling (`_UModel__attribute`)
- Ensures consistent initialization regardless of construction path
- Does not perform any I/O operations

**Example Usage (Internal):**
```python
# Called internally by __init__
self._init_from_components(
    declaration=declaration,
    templates=templates,
    system=system,
    queries=queries,
    model_path=model_path,
    autosave=True
)
```

---

### `_parse_xml()`

**Purpose**: Pure function that parses XML files without side effects.

**Signature:**
```python
@staticmethod
def _parse_xml(model_path: str) -> tuple
```

**Parameters:**
- `model_path` (str): Path to UPPAAL XML model file

**Returns:**
- `tuple`: `(declaration, templates, system, queries)`
  - `declaration` (str): Global declarations (empty string if not present)
  - `templates` (List[Template]): Parsed Template objects
  - `system` (str): System declaration (empty string if not present)
  - `queries` (List[str]): Query strings (empty list if not present)

**Behavior:**
- **Read-only**: Does not modify any files
- **No side effects**: Does not change any global state
- **Always returns lists**: `queries` is always a list, never `None`
- Extracts all components from the XML structure

**Example Usage:**
```python
# Parse XML file
declaration, templates, system, queries = UModel._parse_xml("model.xml")

# Use parsed components
print(f"Found {len(templates)} templates")
print(f"Found {len(queries)} queries")
```

---

## Public APIs

### `__init__(model_path: str = None)`

Constructor for loading models from XML files.

**Parameters:**
- `model_path` (str, optional): Path to UPPAAL XML model file. Defaults to `None`.

**Behavior:**
- If `model_path` is `None`: Creates a new model named `untitled.xml` (legacy behavior with warning)
- If file doesn't exist: Raises `ValueError`
- Otherwise: Loads and parses the XML file
- **Autosave enabled**: Changes to properties automatically save to disk

**Example:**
```python
# Load existing model
model = UModel("my_model.xml")

# Autosave is enabled - this saves automatically
model.declaration = "clock x, y;"
model.queries = "A[] not deadlock"
```

**Raises:**
- `ValueError`: If `model_path` doesn't exist

---

### `from_components(declaration, templates, system, queries=None)`

Class method for creating models from components without requiring an XML file.

**Parameters:**
- `declaration` (str): Global declarations string
- `templates` (List[Template]): List of Template objects
- `system` (str): System declaration string
- `queries` (List[str], optional): Query strings list. Defaults to `None` (becomes `[]`)

**Returns:**
- `UModel`: New UModel instance with autosave disabled

**Behavior:**
- **Autosave disabled**: Changes don't automatically save (no file path required)
- Normalizes `queries=None` to `[]`
- Ideal for programmatic model construction or importing from Python format

**Example:**
```python
from pyuppaal import UModel
from pyuppaal.nta import Template, Location, Edge

# Create template
template = Template(
    name="Process",
    locations=[Location(location_id=0, location_pos=(0, 0), is_initial=True)],
    init_ref=0,
    edges=[]
)

# Create model from components
model = UModel.from_components(
    declaration="clock x;",
    templates=[template],
    system="system Process;",
    queries=["A[] not deadlock"]
)

# Autosave is disabled - must save manually
model.save_as("new_model.xml")
```

---

## Usage Examples

### Example 1: Load and Modify Existing Model

```python
from pyuppaal import UModel

# Load existing model (autosave enabled)
model = UModel("existing_model.xml")

# Modifications automatically save
model.declaration += "\nint counter = 0;"
model.queries = ["E<> counter > 10", "A[] not deadlock"]

# Verify the model
result = model.verify()
print(result)
```

### Example 2: Build Model from Scratch

```python
from pyuppaal import UModel
from pyuppaal.nta import Template, Location, Edge

# Create locations
l0 = Location(location_id=0, location_pos=(0, 0),
              name="Start", is_initial=True)
l1 = Location(location_id=1, location_pos=(100, 0),
              name="Goal")

# Create edge
e0 = Edge(source_location_id=0, target_location_id=1,
          sync="go!", guard="x >= 5", update="x = 0")

# Create template
template = Template(
    name="Process",
    locations=[l0, l1],
    init_ref=0,
    edges=[e0],
    declaration="clock x;"
)

# Build model from components (autosave disabled)
model = UModel.from_components(
    declaration="broadcast chan go;",
    templates=[template],
    system="system Process;",
    queries=["E<> Process.Goal"]
)

# Save when ready
model.save_as("built_model.xml")
```

### Example 3: Import from Python Format

```python
from pyuppaal import UModel

# Import from pyfmt directory (uses from_components internally)
model = UModel.py_fmt_import(
    input_dir="./my_model_pyfmt",
    mode="auto",
    trusted=True
)

# Model is created with autosave disabled
# Save to XML when ready
model.save_as("imported_model.xml")
```

### Example 4: Disable Autosave Temporarily

```python
from pyuppaal import UModel

# Load model with autosave enabled
model = UModel("model.xml")

# Make multiple changes without saving each time
with model.no_autosave():
    model.declaration = "clock x, y, z;"
    model.system = "system P1, P2, P3;"
    model.queries = ["A[] not deadlock"]
# Autosave is restored after the block

# Or save manually
model.save()
```

---

## Migration Guide

### Changes from Previous Implementation

#### 1. Removed `__build()` Method

**Before:**
```python
# Internal method that was called during __init__
self.__build()  # No longer exists
```

**After:**
```python
# Replaced by _parse_xml() - pure function with no side effects
declaration, templates, system, queries = UModel._parse_xml(model_path)
```

#### 2. No Automatic Save on Load

**Before:**
```python
# Loading a model would call save(), modifying the file
model = UModel("model.xml")  # File was modified during load
```

**After:**
```python
# Loading a model only reads the file, no modifications
model = UModel("model.xml")  # File is NOT modified during load
```

#### 3. Queries Always Returns List

**Before:**
```python
model = UModel("model.xml")
if model.queries is None:  # Could be None
    model.queries = []
```

**After:**
```python
model = UModel("model.xml")
# queries is always a list, never None
assert isinstance(model.queries, list)
```

#### 4. from_components() Uses Unified Initialization

**Before:**
```python
# Directly set private attributes with name mangling
instance._UModel__declaration = declaration
instance._UModel__templates = templates
# ... etc
```

**After:**
```python
# Uses unified _init_from_components() method
instance._init_from_components(
    declaration=declaration,
    templates=templates,
    system=system,
    queries=queries,
    model_path=model_path,
    autosave=False
)
```

### Backward Compatibility

The refactoring maintains backward compatibility for all public APIs:

- `UModel(model_path)` works exactly as before
- `UModel.from_components()` no longer accepts `model_path` parameter (removed)
- All properties (`declaration`, `templates`, `system`, `queries`) behave identically
- The only difference: `queries` never returns `None` (always returns `[]` when empty)

### Recommended Updates

While not required, consider these improvements in your code:

```python
# Old style (still works)
if model.queries is not None:
    for query in model.queries:
        print(query)

# New style (recommended)
for query in model.queries:  # queries is always a list
    print(query)
```

---

## Best Practices

### 1. Choose the Right Construction Path

- **Use `UModel(path)`** when working with existing XML files
- **Use `UModel.from_components()`** when building models programmatically or importing from Python format

### 2. Manage Autosave Appropriately

```python
# For XML-based models (autosave enabled)
model = UModel("model.xml")
model.declaration = "..."  # Saves automatically

# For component-based models (autosave disabled)
model = UModel.from_components(...)
model.declaration = "..."  # Does NOT save
model.save_as("model.xml")  # Save manually when ready
```

### 3. Use Context Manager for Batch Updates

```python
# Avoid multiple saves
with model.no_autosave():
    model.declaration = "..."
    model.system = "..."
    model.queries = [...]
# Single save after all changes
```

### 4. Handle Queries Consistently

```python
# Always treat queries as a list
model.queries = ["A[] not deadlock"]  # Single query as list
model.queries = []  # Empty queries

# Iterate safely
for query in model.queries:
    print(query)
```

---

## Technical Details

### Name Mangling

UModel uses Python's name mangling for private attributes:

```python
# Public property
model.declaration

# Internal storage (name mangled)
model._UModel__declaration
```

The `_init_from_components()` method sets these mangled attributes directly to ensure proper initialization.

### Autosave Mechanism

The autosave flag controls whether property setters automatically call `save()`:

```python
@declaration.setter
def declaration(self, value: str) -> None:
    self.__declaration = value
    if self._autosave:  # Check autosave flag
        self.save()
```

### Pure Function Design

`_parse_xml()` is designed as a pure function:
- No side effects
- No file modifications
- Deterministic output for given input
- Can be called multiple times safely

---

## Summary

The UModel construction refactoring provides:

1. **Unified initialization** through `_init_from_components()`
2. **Pure XML parsing** via `_parse_xml()` with no side effects
3. **Consistent behavior** across all construction paths
4. **Predictable queries** that always return `List[str]`
5. **Backward compatibility** with existing code

These improvements make the codebase more maintainable, testable, and predictable while preserving all existing functionality.
