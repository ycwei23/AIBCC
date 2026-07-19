import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["analyses"])


class CopilotRequest(BaseModel):
    question: str


class SimulateRequest(BaseModel):
    patch: list[Any]


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "counts": {"violations": 0, "elements": 0},
    }


@router.get("/analyses/{analysis_id}/violations")
def get_violations(analysis_id: str):
    return []


@router.get("/analyses/{analysis_id}/report")
def get_report(analysis_id: str):
    return {"analysis_id": analysis_id, "report_url": None, "status": "stub"}


@router.post("/analyses/{analysis_id}/copilot")
def copilot(analysis_id: str, body: CopilotRequest):
    return {
        "answer": f"[stub] 針對「{body.question}」的回答尚未實作",
        "citations": [],
        "trace_id": str(uuid.uuid4()),
    }


@router.get("/analyses/{analysis_id}/graph")
def get_graph(analysis_id: str):
    return {"nodes": [], "edges": [], "paths": []}


@router.post("/analyses/{analysis_id}/simulate")
def simulate(analysis_id: str, body: SimulateRequest):
    return {"affected_rules": [], "before": {}, "after": {}}


@router.get("/agent-traces/{trace_id}")
def get_agent_trace(trace_id: str):
    return {
        "trace_id": trace_id,
        "question": "",
        "steps": [],
        "evidence_ids": [],
        "final_rule_status": "pending",
    }
