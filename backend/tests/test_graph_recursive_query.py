import json
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.graph.builder import build_sample_building_graph
from app.graph.recursive_query import query_descendants

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def pg_engine():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip(
            "PostgreSQL not reachable at DATABASE_URL — "
            "start it with `docker compose up -d db` before running this test"
        )
    yield engine
    engine.dispose()


@pytest.fixture
def seeded_graph(pg_engine):
    project_id = str(uuid.uuid4())
    analysis_run_id = str(uuid.uuid4())
    nodes, edges = build_sample_building_graph()

    with pg_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO projects (id, name) VALUES (:id, 'PoC Project')"),
            {"id": project_id},
        )
        conn.execute(
            text(
                "INSERT INTO analysis_runs (id, project_id, status) "
                "VALUES (:id, :project_id, 'uploaded')"
            ),
            {"id": analysis_run_id, "project_id": project_id},
        )
        for node in nodes:
            conn.execute(
                text(
                    "INSERT INTO graph_nodes (analysis_run_id, node_id, node_type, properties) "
                    "VALUES (:analysis_run_id, :node_id, :node_type, :properties)"
                ),
                {
                    "analysis_run_id": analysis_run_id,
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "properties": json.dumps(node.properties),
                },
            )
        for edge in edges:
            conn.execute(
                text(
                    "INSERT INTO graph_edges (analysis_run_id, from_node, relation, to_node, source, confidence) "
                    "VALUES (:analysis_run_id, :from_node, :relation, :to_node, :source, :confidence)"
                ),
                {
                    "analysis_run_id": analysis_run_id,
                    "from_node": edge.from_node,
                    "relation": edge.relation,
                    "to_node": edge.to_node,
                    "source": edge.source,
                    "confidence": edge.confidence,
                },
            )

    yield analysis_run_id

    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM projects WHERE id = :id"), {"id": project_id})


def test_recursive_query_traverses_full_hierarchy(pg_engine, seeded_graph):
    rows = query_descendants(pg_engine, seeded_graph, "building-1")
    reached = {row["to_node"] for row in rows}
    assert reached == {
        "floor-1",
        "space-room-101",
        "space-corridor-1",
        "space-room-103",
        "element-door-101",
        "path-corridor-to-exit",
        "exit-1",
    }


def test_recursive_query_stops_at_dead_end_space(pg_engine, seeded_graph):
    rows = query_descendants(pg_engine, seeded_graph, "space-room-103")
    assert rows == []
