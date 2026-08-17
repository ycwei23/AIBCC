import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import analysis_repo
from app.pipeline.fixtures import list_fixture_keys
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
    pid = analysis_repo.create_project(pg_engine, "E2E Fixture Sweep", "office")
    yield pid
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM projects WHERE id = :id"), {"id": pid})


@pytest.mark.parametrize("fixture_key", list_fixture_keys())
def test_every_fixture_completes_without_crashing(pg_engine, project_id, fixture_key):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, fixture_key)
    row = analysis_repo.get_analysis_run(pg_engine, run_id)
    assert row["status"] in {"completed", "review_required"}


def test_case_04_single_stair_produces_stair_count_fail(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_04_single_stair_fail")
    violations = analysis_repo.get_violations(pg_engine, run_id)
    assert any(v["rule_id"] == "MVP-STAIR-COUNT-95-FLOOR8" and v["status"] == "fail" for v in violations)


def test_case_05_missing_metadata_is_all_insufficient_data(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_05_missing_metadata")
    violations = analysis_repo.get_violations(pg_engine, run_id)
    assert len(violations) > 0
    assert all(v["status"] == "insufficient_data" for v in violations)


def test_case_08_out_of_scope_use_produces_no_d34_violation(pg_engine, project_id):
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_08_out_of_scope_use")
    violations = analysis_repo.get_violations(pg_engine, run_id)
    assert not any(v["rule_id"].startswith("MVP-CORRIDOR-WIDTH-92-D34") for v in violations)
