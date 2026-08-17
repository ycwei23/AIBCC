import json
import uuid

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.graph.builder import GraphEdgeData, GraphNodeData
from app.models.ir import BuildingElement, Violation


def _row_to_dict(row) -> dict:
    """Convert a SQLAlchemy row to a plain dict, stringifying UUID values so results
    are directly JSON-serializable and comparable to plain str ids."""
    return {key: (str(value) if isinstance(value, uuid.UUID) else value) for key, value in row._mapping.items()}


def create_project(engine: Engine, name: str, building_use: str | None) -> str:
    with engine.begin() as conn:
        row = conn.execute(
            text("INSERT INTO projects (name, building_use) VALUES (:name, :building_use) RETURNING id"),
            {"name": name, "building_use": building_use},
        ).first()
        return str(row.id)


def create_file(engine: Engine, project_id: str, storage_path: str, format: str) -> str:
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "INSERT INTO files (project_id, format, hash, storage_path, parse_status) "
                "VALUES (:project_id, :format, :hash, :storage_path, 'pending') RETURNING id"
            ),
            {"project_id": project_id, "format": format, "hash": "n/a", "storage_path": storage_path},
        ).first()
        return str(row.id)


def create_analysis_run(engine: Engine, project_id: str, file_id: str | None) -> str:
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "INSERT INTO analysis_runs (project_id, file_id, status) "
                "VALUES (:project_id, :file_id, 'uploaded') RETURNING id"
            ),
            {"project_id": project_id, "file_id": file_id},
        ).first()
        return str(row.id)


def update_analysis_status(engine: Engine, analysis_run_id: str, status: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE analysis_runs SET status = :status, updated_at = NOW() WHERE id = :id"),
            {"status": status, "id": analysis_run_id},
        )


def save_building_elements(engine: Engine, analysis_run_id: str, elements: list[BuildingElement]) -> None:
    with engine.begin() as conn:
        for element in elements:
            conn.execute(
                text(
                    "INSERT INTO building_elements "
                    "(analysis_run_id, element_id, type, page, bbox, geometry, source, confidence) "
                    "VALUES (:run_id, :element_id, :type, :page, :bbox, :geometry, :source, :confidence)"
                ),
                {
                    "run_id": analysis_run_id,
                    "element_id": element.id,
                    "type": element.type,
                    "page": element.page,
                    "bbox": json.dumps(element.bbox),
                    "geometry": json.dumps(element.geometry),
                    "source": element.source,
                    "confidence": element.confidence,
                },
            )


def save_graph(
    engine: Engine, analysis_run_id: str, nodes: list[GraphNodeData], edges: list[GraphEdgeData]
) -> None:
    with engine.begin() as conn:
        for node in nodes:
            conn.execute(
                text(
                    "INSERT INTO graph_nodes (analysis_run_id, node_id, node_type, properties) "
                    "VALUES (:run_id, :node_id, :node_type, :properties)"
                ),
                {
                    "run_id": analysis_run_id,
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "properties": json.dumps(node.properties),
                },
            )
        for edge in edges:
            conn.execute(
                text(
                    "INSERT INTO graph_edges (analysis_run_id, from_node, relation, to_node, source, confidence) "
                    "VALUES (:run_id, :from_node, :relation, :to_node, :source, :confidence)"
                ),
                {
                    "run_id": analysis_run_id,
                    "from_node": edge.from_node,
                    "relation": edge.relation,
                    "to_node": edge.to_node,
                    "source": edge.source,
                    "confidence": edge.confidence,
                },
            )


def save_violations(engine: Engine, analysis_run_id: str, violations: list[Violation]) -> None:
    with engine.begin() as conn:
        for v in violations:
            conn.execute(
                text(
                    "INSERT INTO violations "
                    "(analysis_run_id, violation_id, rule_id, element_ids, measured, required, "
                    "status, page, highlight, evidence, suggestion) "
                    "VALUES (:run_id, :violation_id, :rule_id, :element_ids, :measured, :required, "
                    ":status, :page, :highlight, :evidence, :suggestion)"
                ),
                {
                    "run_id": analysis_run_id,
                    "violation_id": v.violation_id,
                    "rule_id": v.rule_id,
                    "element_ids": json.dumps(v.element_ids),
                    "measured": v.measured,
                    "required": v.required,
                    "status": v.status,
                    "page": v.page,
                    "highlight": json.dumps(v.highlight),
                    "evidence": v.evidence,
                    "suggestion": v.suggestion,
                },
            )


def get_analysis_run(engine: Engine, analysis_run_id: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM analysis_runs WHERE id = :id"), {"id": analysis_run_id}
        ).first()
        return _row_to_dict(row) if row else None


def get_violations(engine: Engine, analysis_run_id: str) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM violations WHERE analysis_run_id = :id"), {"id": analysis_run_id}
        )
        return [_row_to_dict(row) for row in rows]


def get_graph(engine: Engine, analysis_run_id: str) -> tuple[list[dict], list[dict]]:
    with engine.connect() as conn:
        nodes = [
            _row_to_dict(row)
            for row in conn.execute(
                text("SELECT * FROM graph_nodes WHERE analysis_run_id = :id"), {"id": analysis_run_id}
            )
        ]
        edges = [
            _row_to_dict(row)
            for row in conn.execute(
                text("SELECT * FROM graph_edges WHERE analysis_run_id = :id"), {"id": analysis_run_id}
            )
        ]
        return nodes, edges
