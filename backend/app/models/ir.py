from typing import Any

from pydantic import BaseModel, Field, field_validator


class BuildingElement(BaseModel):
    id: str
    type: str
    page: int
    bbox: list[float]
    geometry: dict[str, Any]
    source: str
    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class Rule(BaseModel):
    rule_id: str
    law_code: str = ""
    law_name: str
    article: str
    version: str
    scope: dict[str, Any]
    target: str
    operator: str
    threshold: float
    unit: str
    severity: str
    source_quote: str = ""


class Violation(BaseModel):
    violation_id: str
    rule_id: str
    element_ids: list[str]
    measured: float
    required: float
    status: str
    page: int
    highlight: list[list[float]]
    evidence: str
    suggestion: str


class GraphEdge(BaseModel):
    from_node: str = Field(alias="from")
    relation: str
    to: str
    source: str
    confidence: float

    model_config = {"populate_by_name": True}


class AgentTrace(BaseModel):
    trace_id: str
    question: str
    steps: list[str]
    evidence_ids: list[str]
    final_rule_status: str
