import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import analysis_repo
from app.pipeline.run_analysis import run_analysis

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
    pid = analysis_repo.create_project(pg_engine, "Pipeline Test Project", "office")
    yield pid
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM projects WHERE id = :id"), {"id": pid})


def test_run_analysis_reaches_completed_status(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_01_clean_pass")
    row = analysis_repo.get_analysis_run(pg_engine, run_id)
    assert row["status"] == "completed"


def test_run_analysis_persists_violations(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_02_narrow_corridor_fail")
    violations = analysis_repo.get_violations(pg_engine, run_id)
    assert any(v["rule_id"] == "MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER" and v["status"] == "fail" for v in violations)


def test_run_analysis_empty_fixture_completes_with_no_violations(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_10_empty")
    row = analysis_repo.get_analysis_run(pg_engine, run_id)
    assert row["status"] == "completed"
    assert analysis_repo.get_violations(pg_engine, run_id) == []


def test_run_analysis_unknown_fixture_marks_failed(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "does_not_exist")
    row = analysis_repo.get_analysis_run(pg_engine, run_id)
    assert row["status"] == "failed"


def test_run_analysis_seeds_rules_table_without_fk_violation(pg_engine, project_id):
    # violations.rule_id has a real FK to rules(rule_id) — this run must not raise
    # ForeignKeyViolation, and the rule row must actually exist afterward.
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_02_narrow_corridor_fail")
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("SELECT rule_id FROM rules WHERE rule_id = 'MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER'")
        ).first()
    assert row is not None
