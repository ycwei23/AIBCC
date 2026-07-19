import pytest
from app.models.ir import BuildingElement, Rule, Violation, GraphEdge, AgentTrace


def test_building_element_valid():
    element = BuildingElement(
        id="door-12",
        type="door",
        page=2,
        bbox=[120.0, 340.0, 188.0, 420.0],
        geometry={"width_mm": 900},
        source="ocr_cv",
        confidence=0.93,
    )
    assert element.id == "door-12"
    assert element.confidence == 0.93


def test_building_element_rejects_confidence_above_one():
    with pytest.raises(Exception):
        BuildingElement(
            id="door-12",
            type="door",
            page=2,
            bbox=[120.0, 340.0, 188.0, 420.0],
            geometry={},
            source="ocr_cv",
            confidence=1.5,
        )


def test_building_element_rejects_negative_confidence():
    with pytest.raises(Exception):
        BuildingElement(
            id="door-12",
            type="door",
            page=2,
            bbox=[120.0, 340.0, 188.0, 420.0],
            geometry={},
            source="ocr_cv",
            confidence=-0.1,
        )


def test_rule_valid():
    rule = Rule(
        rule_id="BTR-EVAC-CORRIDOR-WIDTH-001",
        law_name="建築技術規則",
        article="第九十條",
        version="2026-07-03",
        scope={"building_use": ["office"]},
        target="corridor.width_mm",
        operator=">=",
        threshold=1200.0,
        unit="mm",
        severity="high",
    )
    assert rule.rule_id == "BTR-EVAC-CORRIDOR-WIDTH-001"
    assert rule.threshold == 1200.0


def test_violation_valid():
    v = Violation(
        violation_id="v-001",
        rule_id="BTR-EVAC-CORRIDOR-WIDTH-001",
        element_ids=["corridor-3"],
        measured=980.0,
        required=1200.0,
        status="fail",
        page=2,
        highlight=[[120, 340], [500, 340], [500, 430], [120, 430]],
        evidence="建築技術規則第九十條",
        suggestion="走道淨寬至少增加 220 mm",
    )
    assert v.status == "fail"
    assert v.measured < v.required


def test_graph_edge_valid():
    edge = GraphEdge(**{
        "from": "room-A101",
        "relation": "connected_to",
        "to": "hallway-2",
        "source": "vlm+geometry",
        "confidence": 0.91,
    })
    assert edge.from_node == "room-A101"
    assert edge.relation == "connected_to"
    assert edge.to == "hallway-2"


def test_agent_trace_valid():
    trace = AgentTrace(
        trace_id="trace-001",
        question="走道加寬 200 mm 後是否合法？",
        steps=["query_graph", "simulate_change", "run_rules", "retrieve_law"],
        evidence_ids=["v-001", "law-36"],
        final_rule_status="pass",
    )
    assert trace.trace_id == "trace-001"
    assert len(trace.steps) == 4
