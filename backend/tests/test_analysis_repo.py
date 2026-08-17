import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import analysis_repo
from app.graph.builder import GraphEdgeData, GraphNodeData
from app.models.ir import Violation

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def pg_engine():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("PostgreSQL not reachable — start it with `docker compose up -d db`")
    yield engine
    engine.dispose()


@pytest.fixture
def project_id(pg_engine):
    pid = analysis_repo.create_project(pg_engine, "Repo Test Project", "office")
    yield pid
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM projects WHERE id = :id"), {"id": pid})


@pytest.fixture
def rule_r1(pg_engine):
    # violations.rule_id has a FK to rules(rule_id); seed a minimal rule row so
    # save_violations can reference rule_id="R1" as in the plan's sample test.
    with pg_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO rules (rule_id, law_name, version) "
                "VALUES ('R1', 'Test Law', 'v1') ON CONFLICT (rule_id) DO NOTHING"
            )
        )
    yield "R1"
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM rules WHERE rule_id = 'R1'"))


def test_create_and_get_analysis_run(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    row = analysis_repo.get_analysis_run(pg_engine, run_id)
    assert row["status"] == "uploaded"
    assert row["project_id"] == project_id


def test_update_analysis_status(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    analysis_repo.update_analysis_status(pg_engine, run_id, "rule_checking")
    row = analysis_repo.get_analysis_run(pg_engine, run_id)
    assert row["status"] == "rule_checking"


def test_save_and_get_violations(pg_engine, rule_r1, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    violation = Violation(
        violation_id="v-1", rule_id="R1", element_ids=["e1"], measured=900.0, required=1200.0,
        status="fail", page=1, highlight=[[0, 0, 1, 1]], evidence="法規第一條", suggestion="",
    )
    analysis_repo.save_violations(pg_engine, run_id, [violation])
    rows = analysis_repo.get_violations(pg_engine, run_id)
    assert len(rows) == 1
    assert rows[0]["status"] == "fail"


def test_save_and_get_graph(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    nodes = [GraphNodeData(node_id="n1", node_type="Building", properties={"name": "test"})]
    edges = [GraphEdgeData(from_node="n1", relation="contains", to_node="n2")]
    analysis_repo.save_graph(pg_engine, run_id, nodes, edges)
    got_nodes, got_edges = analysis_repo.get_graph(pg_engine, run_id)
    assert got_nodes[0]["node_id"] == "n1"
    assert got_edges[0]["to_node"] == "n2"
