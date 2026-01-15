"""Test PyExporter with ros2_v01_20251021_temp.xml"""

import os
import shutil
from pyuppaal import UModel
from pyuppaal.py_exporter import PyExporter

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_TRIAL_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(TEST_TRIAL_DIR, "ros2_v01_20251021_temp.xml")
OUTPUT_HUMAN = os.path.join(SCRIPT_DIR, "output", "test_human")
OUTPUT_MACHINE = os.path.join(SCRIPT_DIR, "output", "test_machine")


def test_human_mode():
    """Test human mode export."""
    print("=" * 60)
    print("Testing Human Mode Export")
    print("=" * 60)

    # Clean output directory
    shutil.rmtree(OUTPUT_HUMAN, ignore_errors=True)

    # Load model
    model = UModel(MODEL_PATH)
    print(f"Loaded model with {len(model.templates)} templates:")
    for t in model.templates:
        print(f"  - {t.name}")

    # Export
    PyExporter.export(model, OUTPUT_HUMAN, mode="human", overwrite=True)
    print(f"\nExported to: {OUTPUT_HUMAN}")

    # Verify output
    print("\nGenerated files:")
    for root, dirs, files in os.walk(OUTPUT_HUMAN):
        level = root.replace(OUTPUT_HUMAN, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

    print("\nHuman mode test PASSED!")


def test_machine_mode():
    """Test machine mode export."""
    print("\n" + "=" * 60)
    print("Testing Machine Mode Export")
    print("=" * 60)

    # Clean output directory
    shutil.rmtree(OUTPUT_MACHINE, ignore_errors=True)

    # Load model
    model = UModel(MODEL_PATH)

    # Export
    PyExporter.export(model, OUTPUT_MACHINE, mode="machine", overwrite=True)
    print(f"Exported to: {OUTPUT_MACHINE}")

    # Verify machine mode structure (v2: manifest.toml + JSON payloads)
    assert os.path.exists(os.path.join(OUTPUT_MACHINE, "manifest.toml"))
    assert os.path.exists(os.path.join(OUTPUT_MACHINE, "decl", "decl.json"))
    assert os.path.exists(os.path.join(OUTPUT_MACHINE, "sys_decl", "sys_decl.json"))
    assert os.path.exists(os.path.join(OUTPUT_MACHINE, "queries", "queries.json"))
    for t in model.templates:
        assert os.path.exists(os.path.join(OUTPUT_MACHINE, t.name, f"{t.name}.json"))

    # Smoke-test machine mode import
    imported = UModel.py_fmt_import(OUTPUT_MACHINE, mode="machine")
    print(f"Imported machine mode with {len(imported.templates)} templates")

    # Verify output
    print("\nGenerated files:")
    for root, dirs, files in os.walk(OUTPUT_MACHINE):
        level = root.replace(OUTPUT_MACHINE, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

    # Show manifest.toml content
    manifest_path = os.path.join(OUTPUT_MACHINE, "manifest.toml")
    if os.path.exists(manifest_path):
        print("\nmanifest.toml content:")
        print("-" * 40)
        with open(manifest_path, "r") as f:
            print(f.read())

    print("Machine mode test PASSED!")


def test_overwrite_protection():
    """Test overwrite protection."""
    print("\n" + "=" * 60)
    print("Testing Overwrite Protection")
    print("=" * 60)

    model = UModel(MODEL_PATH)

    # First export should succeed
    shutil.rmtree(OUTPUT_HUMAN, ignore_errors=True)
    PyExporter.export(model, OUTPUT_HUMAN, mode="human", overwrite=True)

    # Second export without overwrite should fail
    try:
        PyExporter.export(model, OUTPUT_HUMAN, mode="human", overwrite=False)
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print(f"Correctly raised ValueError: {e}")
        print("Overwrite protection test PASSED!")


def test_umodel_interface():
    """Test UModel.py_fmt_export() interface."""
    print("\n" + "=" * 60)
    print("Testing UModel.py_fmt_export() Interface")
    print("=" * 60)

    model = UModel(MODEL_PATH)

    # Test human mode via UModel interface
    output_human = os.path.join(SCRIPT_DIR, "output", "test_umodel_human")
    shutil.rmtree(output_human, ignore_errors=True)
    model.py_fmt_export(output_human, mode="human")
    print(f"Human mode exported to: {output_human}")

    # Verify human mode output
    assert os.path.exists(os.path.join(output_human, "registry.py"))
    assert os.path.exists(os.path.join(output_human, "__init__.py"))
    assert os.path.exists(os.path.join(output_human, "decl", "decl.txt"))
    print("  [OK] Human mode structure verified")

    # Test machine mode via UModel interface
    output_machine = os.path.join(SCRIPT_DIR, "output", "test_umodel_machine")
    shutil.rmtree(output_machine, ignore_errors=True)
    model.py_fmt_export(output_machine, mode="machine")
    print(f"Machine mode exported to: {output_machine}")

    # Verify machine mode output
    assert os.path.exists(os.path.join(output_machine, "manifest.toml"))
    assert os.path.exists(os.path.join(output_machine, "decl", "decl.json"))
    assert os.path.exists(os.path.join(output_machine, "sys_decl", "sys_decl.json"))
    print("  [OK] Machine mode structure verified")

    # Test default mode (should be human)
    output_default = os.path.join(SCRIPT_DIR, "output", "test_umodel_default")
    shutil.rmtree(output_default, ignore_errors=True)
    model.py_fmt_export(output_default)
    print(f"Default mode exported to: {output_default}")

    # Verify default mode is human
    assert os.path.exists(os.path.join(output_default, "registry.py"))
    assert os.path.exists(os.path.join(output_default, "__init__.py"))
    print("  [OK] Default mode (human) verified")

    print("\nUModel interface test PASSED!")


if __name__ == "__main__":
    test_human_mode()
    test_machine_mode()
    test_overwrite_protection()
    test_umodel_interface()
    print("\n" + "=" * 60)
    print("All tests PASSED!")
    print("=" * 60)
