"""Test PyImporter with test_trial outputs."""

import os
from pyuppaal import UModel
from pyuppaal.py_importer import PyImporter
from pyuppaal.py_exporter import PyExporter

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_TRIAL_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(TEST_TRIAL_DIR, "ros2_v01_20251021_temp.xml")
INPUT_HUMAN = os.path.join(SCRIPT_DIR, "output", "test_human")
INPUT_MACHINE = os.path.join(SCRIPT_DIR, "output", "test_machine")


def _ensure_exports():
    if os.path.isdir(INPUT_HUMAN) and os.path.isdir(INPUT_MACHINE):
        return

    model = UModel(MODEL_PATH)
    os.makedirs(os.path.join(SCRIPT_DIR, "output"), exist_ok=True)
    PyExporter.export(model, INPUT_HUMAN, mode="human", overwrite=True)
    PyExporter.export(model, INPUT_MACHINE, mode="machine", overwrite=True)


def test_human_mode_import():
    """Test human mode import (trusted)."""
    print("=" * 60)
    print("Testing Human Mode Import (trusted)")
    print("=" * 60)

    _ensure_exports()

    # Import from human mode directory with trusted=True
    umodel = PyImporter.import_dir(INPUT_HUMAN, mode="human", trusted=True)

    print(f"Imported model with {len(umodel.templates)} templates:")
    for t in umodel.templates:
        print(f"  - {t.name} ({len(t.locations)} locations, {len(t.edges)} edges)")

    # Verify basic structure
    assert len(umodel.templates) > 0, "Should have at least one template"
    assert umodel.declaration is not None, "Should have declaration"
    assert umodel.system is not None, "Should have system"

    print("\nHuman mode import test PASSED!")
    return umodel


def test_machine_mode_import():
    """Test machine mode import."""
    print("\n" + "=" * 60)
    print("Testing Machine Mode Import")
    print("=" * 60)

    _ensure_exports()

    umodel = PyImporter.import_dir(INPUT_MACHINE, mode="machine")

    print(f"Imported model with {len(umodel.templates)} templates:")
    for t in umodel.templates:
        print(f"  - {t.name} ({len(t.locations)} locations, {len(t.edges)} edges)")

    assert len(umodel.templates) > 0, "Should have at least one template"
    assert umodel.declaration is not None, "Should have declaration"
    assert umodel.system is not None, "Should have system"

    print("\nMachine mode import test PASSED!")
    return umodel


def test_machine_mode_import_save_xml():
    """Test machine mode import and save as XML."""
    print("\n" + "=" * 60)
    print("Testing Machine Mode Import -> Save XML")
    print("=" * 60)

    _ensure_exports()

    output_xml = os.path.join(SCRIPT_DIR, "output", "imported_machine.xml")
    umodel = PyImporter.import_dir(
        INPUT_MACHINE,
        mode="machine",
        output_xml_path=output_xml,
        overwrite=True,
    )

    assert os.path.exists(output_xml), "Should have written XML output"
    assert os.path.getsize(output_xml) > 0, "XML output should not be empty"

    reloaded = UModel(output_xml)
    assert len(reloaded.templates) == len(umodel.templates), "Reloaded XML should preserve templates"

    print(f"Saved and reloaded XML: {output_xml}")
    print("\nMachine mode import->save XML test PASSED!")


def test_trust_security():
    """Test trust security for human mode."""
    print("\n" + "=" * 60)
    print("Testing Trust Security")
    print("=" * 60)

    # Human mode without trusted should fail
    try:
        PyImporter.import_dir(INPUT_HUMAN, mode="human", trusted=False)
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print(f"Correctly raised ValueError: {e}")
        print("Trust security test PASSED!")


def test_umodel_interface():
    """Test UModel.py_fmt_import() interface."""
    print("\n" + "=" * 60)
    print("Testing UModel.py_fmt_import() Interface")
    print("=" * 60)

    _ensure_exports()

    # Test human mode via UModel interface
    umodel = UModel.py_fmt_import(INPUT_HUMAN, mode="human", trusted=True)
    print(f"Imported via UModel interface: {len(umodel.templates)} templates")

    assert len(umodel.templates) > 0, "Should have templates"
    print("\nUModel interface test PASSED!")

    # Test machine mode via UModel interface
    umodel_machine = UModel.py_fmt_import(INPUT_MACHINE, mode="machine")
    print(f"Imported machine via UModel interface: {len(umodel_machine.templates)} templates")

    assert len(umodel_machine.templates) > 0, "Should have templates"


if __name__ == "__main__":
    test_human_mode_import()
    test_machine_mode_import()
    test_machine_mode_import_save_xml()
    test_trust_security()
    test_umodel_interface()
    print("\n" + "=" * 60)
    print("All tests PASSED!")
    print("=" * 60)
