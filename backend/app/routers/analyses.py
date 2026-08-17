import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.db import analysis_repo
from app.db.session import engine

router = APIRouter(prefix="/v1", tags=["analyses"])


class CopilotRequest(BaseModel):
    question: str


class SimulateRequest(BaseModel):
    patch: list[Any]


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    row = analysis_repo.get_analysis_run(engine, analysis_id)
    if row is None:
        return {"analysis_id": analysis_id, "status": "not_found", "counts": {"violations": 0, "elements": 0}}
    violations = analysis_repo.get_violations(engine, analysis_id)
    nodes, _edges = analysis_repo.get_graph(engine, analysis_id)
    return {
        "analysis_id": analysis_id,
        "status": row["status"],
        "counts": {"violations": len(violations), "elements": len(nodes)},
    }


@router.get("/analyses/{analysis_id}/violations")
def get_violations(analysis_id: str):
    return analysis_repo.get_violations(engine, analysis_id)


@router.get("/analyses/{analysis_id}/report")
def get_report(analysis_id: str):
    row = analysis_repo.get_analysis_run(engine, analysis_id)
    violations = analysis_repo.get_violations(engine, analysis_id)
    fail_count = sum(1 for v in violations if v["status"] == "fail")
    status = row["status"] if row else "not_found"
    return {
        "analysis_id": analysis_id,
        "report_url": None,
        "status": status,
        "summary": f"{len(violations)} 條規則檢查，{fail_count} 條不符合",
    }


@router.post("/analyses/{analysis_id}/copilot")
def copilot(analysis_id: str, body: CopilotRequest):
    return {
        "answer": f"[stub] 針對「{body.question}」的回答尚未實作",
        "citations": [],
        "trace_id": str(uuid.uuid4()),
    }


@router.get("/analyses/{analysis_id}/graph")
def get_graph(analysis_id: str):
    nodes, edges = analysis_repo.get_graph(engine, analysis_id)
    return {"nodes": nodes, "edges": edges, "paths": []}


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
