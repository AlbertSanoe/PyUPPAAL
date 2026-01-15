import pytest

from pyuppaal.simple_builder import ModelBuilder


def _get_loc_by_name(template, name):
    for loc in template.locations:
        if loc.name == name:
            return loc
    raise AssertionError(f"Location not found: {name}")


def test_builder_ids_and_positions_unique():
    mb = ModelBuilder()
    t1 = mb.template("T1")
    t1.location("A", initial=True)
    t1.location("B")
    t2 = mb.template("T2")
    t2.location("C", initial=True)
    t2.location("D")

    templates = mb.build_templates()
    ids = []
    for template in templates:
        for loc in template.locations:
            ids.append(loc.location_id)
            assert isinstance(loc.location_pos, tuple)
            assert len(loc.location_pos) == 2

    assert len(ids) == len(set(ids))


def test_builder_edge_resolves_names():
    mb = ModelBuilder()
    t = mb.template("Proc")
    t.location("Start", initial=True)
    t.location("End")
    t.edge("Start", "End", guard="x < 5")

    template = t.to_template()
    edge = template.edges[0]
    start = _get_loc_by_name(template, "Start")
    end = _get_loc_by_name(template, "End")

    assert edge.source_location_id == start.location_id
    assert edge.target_location_id == end.location_id
    assert edge.source_location_pos == start.location_pos
    assert edge.target_location_pos == end.location_pos


def test_builder_requires_initial():
    mb = ModelBuilder()
    t = mb.template("T")
    t.location("A")

    with pytest.raises(ValueError):
        t.to_template()


def test_builder_rejects_multiple_initial():
    mb = ModelBuilder()
    t = mb.template("T")
    t.location("A", initial=True)

    with pytest.raises(ValueError):
        t.location("B", initial=True)
