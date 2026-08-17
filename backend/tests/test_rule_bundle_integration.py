"""Integration tests against the real building-law-etl MVP rule bundle.

Unlike test_rule_loader.py / test_rule_engine.py (hand-written single-rule
fixtures), these load the actual vendored data/rules/mvp_rules_active_v0.json
and run it through run_rules() to prove the real 11-rule file parses and
evaluates correctly end to end.
"""

from pathlib import Path

from app.models.ir import BuildingElement
from app.rules.engine import run_rules
from app.rules.loader import load_rules_from_file

MVP_BUNDLE_PATH = Path(__file__).resolve().parents[1] / "data" / "rules" / "mvp_rules_active_v0.json"

EXPECTED_RULE_IDS = {
    "MVP-EXIT-WIDTH-90",
    "MVP-EXIT-HEIGHT-90",
    "MVP-EXIT-WIDTH-91",
    "MVP-CORRIDOR-WIDTH-92-D34-BOTH",
    "MVP-CORRIDOR-WIDTH-92-D34-OTHER",
    "MVP-CORRIDOR-WIDTH-92-DEFAULT-BOTH",
    "MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER",
    "MVP-EVAC-WALK-93-ABD1",
    "MVP-EVAC-WALK-93-C",
    "MVP-EVAC-WALK-93-OTHER",
    "MVP-STAIR-COUNT-95-FLOOR8",
}


def test_real_mvp_bundle_loads_all_11_active_rules():
    rules = load_rules_from_file(MVP_BUNDLE_PATH)

    assert len(rules) == 11
    assert {rule.rule_id for rule in rules} == EXPECTED_RULE_IDS


def test_run_rules_against_current_benchmark_schema_elements_is_honest_about_missing_scope_metadata():
    """Elements built exactly per today's Document AI benchmark annotation schema
    (door/corridor/stair/room/exit_entrance geometry only — no floor-level
    building_use / is_evacuation_floor / both_sides_habitable / room_floor_area_sqm).
    Every MVP rule has a scope condition gated on that metadata, so today's honest
    result is insufficient_data, not a guessed pass/fail.
    """
    rules = load_rules_from_file(MVP_BUNDLE_PATH)
    elements = [
        BuildingElement(
            id="exit_001",
            type="exit_entrance",
            page=1,
            bbox=[50.0, 200.0, 90.0, 230.0],
            geometry={"width_mm": 1200, "height_mm": 2000},
            source="benchmark_fixture",
            confidence=1.0,
        ),
        BuildingElement(
            id="corridor_A_01",
            type="corridor",
            page=1,
            bbox=[100.0, 200.0, 400.0, 260.0],
            geometry={"width_mm": 1500},
            source="benchmark_fixture",
            confidence=1.0,
        ),
        BuildingElement(
            id="stair_001",
            type="stair",
            page=1,
            bbox=[500.0, 300.0, 560.0, 350.0],
            geometry={},
            source="benchmark_fixture",
            confidence=1.0,
        ),
    ]

    violations = run_rules(elements, rules)

    assert len(violations) > 0
    assert {v.status for v in violations} == {"insufficient_data"}


def test_run_rules_produces_real_pass_fail_once_scope_metadata_is_supplied():
    rules = load_rules_from_file(MVP_BUNDLE_PATH)
    elements = [
        BuildingElement(
            id="corridor_A_01",
            type="corridor",
            page=1,
            bbox=[100.0, 200.0, 400.0, 260.0],
            geometry={"width_mm": 900},
            source="benchmark_fixture",
            confidence=1.0,
            metadata={"both_sides_habitable": False, "building_use": "B-2"},
        ),
        BuildingElement(
            id="stair_001",
            type="stair",
            page=8,
            bbox=[500.0, 300.0, 560.0, 350.0],
            geometry={},
            source="benchmark_fixture",
            confidence=1.0,
            metadata={"floor_index": 8},
        ),
        BuildingElement(
            id="stair_002",
            type="stair",
            page=8,
            bbox=[600.0, 300.0, 660.0, 350.0],
            geometry={},
            source="benchmark_fixture",
            confidence=1.0,
            metadata={"floor_index": 8},
        ),
    ]

    violations = run_rules(elements, rules)

    corridor_violation = next(v for v in violations if v.rule_id == "MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER")
    assert corridor_violation.status == "fail"

    stair_violation = next(v for v in violations if v.rule_id == "MVP-STAIR-COUNT-95-FLOOR8")
    assert stair_violation.status == "pass"
