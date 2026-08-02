from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from app.graph.builder import GraphEdgeData, GraphNodeData
from app.ingest.document_ai_adapter import LayoutBlock
from app.ingest.vlm_adapter import VlmDetection, VlmRelation
from app.models.ir import BuildingElement, Rule, Violation


class ToolName(StrEnum):
    PARSE_DOCUMENT = "parse_document"
    EXTRACT_BUILDING_IR = "extract_building_ir"
    VALIDATE_GEOMETRY = "validate_geometry"
    RETRIEVE_LAW = "retrieve_law"
    QUERY_GRAPH = "query_graph"
    RUN_RULES = "run_rules"
    SIMULATE_CHANGE = "simulate_change"
    GENERATE_REPORT = "generate_report"


TOOL_WHITELIST: frozenset[str] = frozenset(tool.value for tool in ToolName)


class ParseDocumentInput(BaseModel):
    file_id: str
    storage_path: str
    format: str


class ParseDocumentOutput(BaseModel):
    file_id: str
    pages: int
    layout_blocks: list[LayoutBlock]


class ExtractBuildingIrInput(BaseModel):
    file_id: str
    layout_blocks: list[LayoutBlock]
    vlm_detections: list[VlmDetection]
    vlm_relations: list[VlmRelation]


class ExtractBuildingIrOutput(BaseModel):
    elements: list[BuildingElement]
    edges: list[GraphEdgeData]


class GeometryError(BaseModel):
    element_id: str
    error_type: str
    message: str


class ValidateGeometryInput(BaseModel):
    elements: list[BuildingElement]


class ValidateGeometryOutput(BaseModel):
    valid_elements: list[BuildingElement]
    geometry_errors: list[GeometryError]


class RetrieveLawInput(BaseModel):
    query: str
    building_use: str | None = None
    top_k: int = 5


class LawMatch(BaseModel):
    rule_id: str
    law_name: str
    article: str
    snippet: str
    relevance_score: float


class RetrieveLawOutput(BaseModel):
    matches: list[LawMatch]


class QueryGraphInput(BaseModel):
    analysis_run_id: str
    start_node_id: str
    max_depth: int = 10


class QueryGraphOutput(BaseModel):
    nodes: list[GraphNodeData]
    edges: list[GraphEdgeData]


class RunRulesInput(BaseModel):
    elements: list[BuildingElement]
    rules: list[Rule]


class RunRulesOutput(BaseModel):
    violations: list[Violation]


class SimulateChangeInput(BaseModel):
    analysis_run_id: str
    patch: list[dict[str, Any]]


class SimulateChangeOutput(BaseModel):
    affected_rule_ids: list[str]
    before_status: dict[str, str]
    after_status: dict[str, str]


class GenerateReportInput(BaseModel):
    analysis_run_id: str
    violations: list[Violation]
    trace_id: str


class GenerateReportOutput(BaseModel):
    report_url: str | None
    summary: str
