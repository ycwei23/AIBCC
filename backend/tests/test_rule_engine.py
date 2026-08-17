from app.models.ir import BuildingElement, Rule
from app.rules.engine import run_rules


def _element(**overrides):
    base = dict(
        id="el-1",
        type="exit",
        page=1,
        bbox=[0, 0, 1, 1],
        geometry={},
        source="vlm",
        confidence=0.9,
        metadata={},
    )
    base.update(overrides)
    return BuildingElement(**base)


def _rule(**overrides):
    base = dict(
        rule_id="R1",
        law_code="D0070115",
        law_name="建築技術規則建築設計施工編",
        article="90",
        version="2026-02-23",
        scope={},
        target="exit.width_mm",
        operator=">=",
        threshold=1200.0,
        unit="mm",
        severity="high",
        source_quote="",
    )
    base.update(overrides)
    return Rule(**base)


def test_t1_exit_width_pass_on_evacuation_floor():
    rule = _rule(scope={"conditions": ["location=evacuation_floor"]})
    element = _element(geometry={"width_mm": 1500}, metadata={"is_evacuation_floor": True})

    violations = run_rules([element], [rule])

    assert len(violations) == 1
    assert violations[0].status == "pass"
    assert violations[0].measured == 1500


def test_t2_exit_width_fail_on_evacuation_floor():
    rule = _rule(scope={"conditions": ["location=evacuation_floor"]})
    element = _element(geometry={"width_mm": 1100}, metadata={"is_evacuation_floor": True})

    violations = run_rules([element], [rule])

    assert violations[0].status == "fail"


def test_t3_corridor_width_pass_default_other():
    rule = _rule(
        rule_id="MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER",
        target="corridor.width_mm",
        threshold=1200.0,
        scope={"conditions": ["corridor.other", "exclude=D-3,D-4,D-5,F-1"]},
    )
    element = _element(
        type="corridor",
        geometry={"width_mm": 1200},
        metadata={"both_sides_habitable": False, "building_use": "B-2"},
    )

    violations = run_rules([element], [rule])

    assert violations[0].status == "pass"


def test_t4_corridor_width_fail_default_other():
    rule = _rule(
        rule_id="MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER",
        target="corridor.width_mm",
        threshold=1200.0,
        scope={"conditions": ["corridor.other", "exclude=D-3,D-4,D-5,F-1"]},
    )
    element = _element(
        type="corridor",
        geometry={"width_mm": 980},
        metadata={"both_sides_habitable": False, "building_use": "B-2"},
    )

    violations = run_rules([element], [rule])

    assert violations[0].status == "fail"


def test_t5_evac_walk_pass():
    rule = _rule(
        rule_id="MVP-EVAC-WALK-93-ABD1",
        target="evac.walking_distance_m",
        operator="<=",
        threshold=30.0,
        unit="m",
        scope={"building_use": ["A", "B-1", "B-2", "B-3", "D-1"], "conditions": ["floor!=evacuation_floor"]},
    )
    element = _element(
        type="room",
        geometry={"walking_distance_m": 28},
        metadata={"building_use": "B-2", "is_evacuation_floor": False},
    )

    violations = run_rules([element], [rule])

    assert violations[0].status == "pass"


def test_t6_evac_walk_fail():
    rule = _rule(
        rule_id="MVP-EVAC-WALK-93-ABD1",
        target="evac.walking_distance_m",
        operator="<=",
        threshold=30.0,
        unit="m",
        scope={"building_use": ["A", "B-1", "B-2", "B-3", "D-1"], "conditions": ["floor!=evacuation_floor"]},
    )
    element = _element(
        type="room",
        geometry={"walking_distance_m": 35},
        metadata={"building_use": "B-2", "is_evacuation_floor": False},
    )

    violations = run_rules([element], [rule])

    assert violations[0].status == "fail"


def test_t7_stair_count_pass():
    rule = _rule(
        rule_id="MVP-STAIR-COUNT-95-FLOOR8",
        target="stair.count",
        operator=">=",
        threshold=2.0,
        unit="count",
        scope={"conditions": ["floor_index>=8"]},
    )
    elements = [
        _element(id="stair-1", type="stair", page=10, metadata={"floor_index": 10}),
        _element(id="stair-2", type="stair", page=10, metadata={"floor_index": 10}),
    ]

    violations = run_rules(elements, [rule])

    assert len(violations) == 1
    assert violations[0].status == "pass"
    assert violations[0].measured == 2
    assert set(violations[0].element_ids) == {"stair-1", "stair-2"}


def test_t8_stair_count_fail():
    rule = _rule(
        rule_id="MVP-STAIR-COUNT-95-FLOOR8",
        target="stair.count",
        operator=">=",
        threshold=2.0,
        unit="count",
        scope={"conditions": ["floor_index>=8"]},
    )
    elements = [_element(id="stair-1", type="stair", page=10, metadata={"floor_index": 10})]

    violations = run_rules(elements, [rule])

    assert violations[0].status == "fail"


def test_out_of_scope_building_use_produces_no_violation():
    rule = _rule(scope={"building_use": ["A"]})
    element = _element(geometry={"width_mm": 1500}, metadata={"building_use": "B-2"})

    assert run_rules([element], [rule]) == []


def test_missing_scope_metadata_produces_insufficient_data_not_a_false_pass():
    rule = _rule(scope={"conditions": ["location=evacuation_floor"]})
    element = _element(geometry={"width_mm": 1500}, metadata={})

    violations = run_rules([element], [rule])

    assert violations[0].status == "insufficient_data"


def test_missing_geometry_field_produces_insufficient_data():
    rule = _rule()
    element = _element(geometry={}, metadata={})

    violations = run_rules([element], [rule])

    assert violations[0].status == "insufficient_data"


def test_unknown_target_prefix_is_skipped():
    rule = _rule(target="ramp.slope_ratio")
    element = _element(type="ramp", geometry={"slope_ratio": "1:10"})

    assert run_rules([element], [rule]) == []
