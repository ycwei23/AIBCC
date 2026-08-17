import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.agent.planner import fixed_sequence_planner, template_answerer
from app.agent.state_machine import AgentStateMachine
from app.agent.tool_executor import build_tool_executor
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
def analyzed_run(pg_engine):
    project_id = analysis_repo.create_project(pg_engine, "Agent Test Project", "office")
    run_id = analysis_repo.create_analysis_run(pg_engine, project_id, None)
    run_analysis(pg_engine, run_id, "case_02_narrow_corridor_fail")
    yield run_id
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM projects WHERE id = :id"), {"id": project_id})


def test_agent_state_machine_answers_with_real_violation_data(pg_engine, analyzed_run):
    tool_executor = build_tool_executor(pg_engine, analyzed_run)
    machine = AgentStateMachine(
        planner=fixed_sequence_planner, tool_executor=tool_executor, answerer=template_answerer
    )
    result = machine.run("走廊淨寬是否符合規定？")
    assert result.final_state == "done"
    assert "fail" in result.answer or "不符合" in result.answer
    assert len(result.steps) >= 2
