from app.agent.tools import (
    TOOL_WHITELIST,
    ExtractBuildingIrInput,
    ExtractBuildingIrOutput,
    GenerateReportInput,
    GenerateReportOutput,
    LawMatch,
    ParseDocumentInput,
    ParseDocumentOutput,
    QueryGraphInput,
    QueryGraphOutput,
    RetrieveLawInput,
    RetrieveLawOutput,
    RunRulesInput,
    RunRulesOutput,
    SimulateChangeInput,
    SimulateChangeOutput,
    ToolName,
    ValidateGeometryInput,
    ValidateGeometryOutput,
)
from app.graph.builder import GraphEdgeData, GraphNodeData
from app.ingest.document_ai_adapter import LayoutBlock
from app.ingest.vlm_adapter import VlmDetection, VlmRelation
from app.models.ir import BuildingElement, Rule, Violation


def test_tool_whitelist_matches_milestone_spec():
    assert TOOL_WHITELIST == frozenset(
        {
            "parse_document",
            "extract_building_ir",
            "validate_geometry",
            "retrieve_law",
            "query_graph",
            "run_rules",
            "simulate_change",
            "generate_report",
        }
    )
    assert len(TOOL_WHITELIST) == 8
    assert ToolName.PARSE_DOCUMENT.value == "parse_document"


def test_parse_document_io_roundtrip():
    inp = ParseDocumentInput(file_id="file-1", storage_path="/data/file-1.pdf", format="pdf")
    out = ParseDocumentOutput(
        file_id="file-1",
        pages=3,
        layout_blocks=[
            LayoutBlock(
                block_id="b1", page=1, bbox=[0, 0, 10, 10], block_type="text", text="x", ocr_confidence=0.9
            )
        ],
    )
    assert inp.format == "pdf"
    assert out.pages == 3
    assert len(out.layout_blocks) == 1


def test_extract_building_ir_io_roundtrip():
    inp = ExtractBuildingIrInput(
        file_id="file-1",
        layout_blocks=[],
        vlm_detections=[
            VlmDetection(detection_id="d1", page=1, bbox=[0, 0, 1, 1], label="room", confidence=0.9)
        ],
        vlm_relations=[
            VlmRelation(from_detection_id="d1", relation="connected_to", to_detection_id="d2", confidence=0.8)
        ],
    )
    out = ExtractBuildingIrOutput(
        elements=[
            BuildingElement(
                id="d1", type="room", page=1, bbox=[0, 0, 1, 1], geometry={}, source="vlm", confidence=0.9
            )
        ],
        edges=[GraphEdgeData(from_node="d1", relation="connected_to", to_node="d2")],
    )
    assert inp.vlm_detections[0].detection_id == "d1"
    assert out.elements[0].type == "room"
    assert out.edges[0].to_node == "d2"


def test_validate_geometry_io_roundtrip():
    element = BuildingElement(
        id="e1", type="door", page=1, bbox=[0, 0, 1, 1], geometry={}, source="vlm", confidence=0.9
    )
    inp = ValidateGeometryInput(elements=[element])
    out = ValidateGeometryOutput(valid_elements=[element], geometry_errors=[])
    assert inp.elements[0].id == "e1"
    assert out.geometry_errors == []


def test_retrieve_law_io_roundtrip():
    inp = RetrieveLawInput(query="走道淨寬", building_use="office", top_k=3)
    out = RetrieveLawOutput(
        matches=[
            LawMatch(
                rule_id="BTR-EVAC-CORRIDOR-WIDTH-001",
                law_name="建築技術規則",
                article="第九十條",
                snippet="走道淨寬不得小於...",
                relevance_score=0.95,
            )
        ]
    )
    assert inp.top_k == 3
    assert out.matches[0].rule_id == "BTR-EVAC-CORRIDOR-WIDTH-001"


def test_query_graph_io_roundtrip():
    inp = QueryGraphInput(analysis_run_id="run-1", start_node_id="building-1", max_depth=5)
    out = QueryGraphOutput(
        nodes=[GraphNodeData(node_id="building-1", node_type="Building")],
        edges=[GraphEdgeData(from_node="building-1", relation="contains", to_node="floor-1")],
    )
    assert inp.max_depth == 5
    assert out.nodes[0].node_type == "Building"


def test_run_rules_io_roundtrip():
    element = BuildingElement(
        id="e1", type="corridor", page=1, bbox=[0, 0, 1, 1], geometry={}, source="vlm", confidence=0.9
    )
    rule = Rule(
        rule_id="R1",
        law_name="建築技術規則",
        article="第九十條",
        version="2026-07-03",
        scope={},
        target="corridor.width_mm",
        operator=">=",
        threshold=1200.0,
        unit="mm",
        severity="high",
    )
    inp = RunRulesInput(elements=[element], rules=[rule])
    out = RunRulesOutput(
        violations=[
            Violation(
                violation_id="v1",
                rule_id="R1",
                element_ids=["e1"],
                measured=900.0,
                required=1200.0,
                status="fail",
                page=1,
                highlight=[[0, 0], [1, 1]],
                evidence="建築技術規則第九十條",
                suggestion="加寬走道",
            )
        ]
    )
    assert inp.rules[0].rule_id == "R1"
    assert out.violations[0].status == "fail"


def test_simulate_change_io_roundtrip():
    inp = SimulateChangeInput(
        analysis_run_id="run-1", patch=[{"op": "replace", "path": "/corridor-3/width_mm", "value": 1400}]
    )
    out = SimulateChangeOutput(
        affected_rule_ids=["R1"], before_status={"R1": "fail"}, after_status={"R1": "pass"}
    )
    assert inp.patch[0]["value"] == 1400
    assert out.after_status["R1"] == "pass"


def test_generate_report_io_roundtrip():
    inp = GenerateReportInput(analysis_run_id="run-1", violations=[], trace_id="trace-1")
    out = GenerateReportOutput(report_url=None, summary="0 violations found")
    assert inp.trace_id == "trace-1"
    assert out.report_url is None
