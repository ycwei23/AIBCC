import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# POST /v1/projects
@pytest.mark.integration
def test_create_project_persists_to_db():
    response = client.post("/v1/projects", json={"name": "Test Building", "building_use": "office"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Building"
    assert data["building_use"] == "office"
    # id must be a real DB-generated UUID, not a random client-side stub
    assert len(data["id"]) == 36


@pytest.mark.integration
def test_start_analysis_runs_pipeline_synchronously():
    project = client.post("/v1/projects", json={"name": "Pipeline Route Test"}).json()
    response = client.post(
        f"/v1/projects/{project['id']}/analyses", json={"fixture_key": "case_01_clean_pass"}
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "completed"


# POST /v1/projects/{id}/files
@pytest.mark.integration
def test_upload_file_stub():
    project = client.post("/v1/projects", json={"name": "Upload Route Test"}).json()
    response = client.post(
        f"/v1/projects/{project['id']}/files",
        files={"file": ("plan.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 202
    data = response.json()
    assert "file_id" in data
    assert data["status"] == "pending"


# GET /v1/analyses/{id}
@pytest.mark.integration
def test_get_analysis_unknown_id_returns_not_found_shape():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_found"
    assert data["counts"] == {"violations": 0, "elements": 0}


@pytest.mark.integration
def test_get_analysis_returns_real_status_and_counts():
    project = client.post("/v1/projects", json={"name": "Get Analysis Test"}).json()
    started = client.post(
        f"/v1/projects/{project['id']}/analyses", json={"fixture_key": "case_02_narrow_corridor_fail"}
    ).json()
    response = client.get(f"/v1/analyses/{started['analysis_id']}")
    data = response.json()
    assert data["status"] == "completed"
    assert data["counts"]["violations"] >= 1


# GET /v1/analyses/{id}/violations
@pytest.mark.integration
def test_get_violations_unknown_id_returns_empty_list():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}/violations")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_get_violations_returns_real_fail_status():
    project = client.post("/v1/projects", json={"name": "Get Violations Test"}).json()
    started = client.post(
        f"/v1/projects/{project['id']}/analyses", json={"fixture_key": "case_02_narrow_corridor_fail"}
    ).json()
    response = client.get(f"/v1/analyses/{started['analysis_id']}/violations")
    violations = response.json()
    assert any(v["rule_id"] == "MVP-CORRIDOR-WIDTH-92-DEFAULT-OTHER" and v["status"] == "fail" for v in violations)


# GET /v1/analyses/{id}/report
@pytest.mark.integration
def test_get_report_unknown_id_returns_not_found_summary():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}/report")
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == analysis_id
    assert data["status"] == "not_found"


# GET /v1/rules
def test_get_rules_stub():
    response = client.get("/v1/rules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# POST /v1/analyses/{id}/copilot
@pytest.mark.integration
def test_copilot_unknown_analysis_returns_empty_answer_shape():
    analysis_id = str(uuid.uuid4())
    response = client.post(
        f"/v1/analyses/{analysis_id}/copilot",
        json={"question": "走道加寬 200mm 後是否合法？"},
    )
    assert response.status_code == 200
    data = response.json()
    # Unknown analysis_id is a foreign-key guard clause, not a pipeline run —
    # copilot returns a clean empty shape instead of hitting the agent state machine.
    assert data == {"answer": "", "citations": [], "trace_id": None}


# GET /v1/analyses/{id}/graph
@pytest.mark.integration
def test_get_graph_unknown_id_returns_empty_graph():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["nodes"] == []
    assert data["edges"] == []


@pytest.mark.integration
def test_get_graph_returns_real_nodes():
    project = client.post("/v1/projects", json={"name": "Get Graph Test"}).json()
    started = client.post(
        f"/v1/projects/{project['id']}/analyses", json={"fixture_key": "case_01_clean_pass"}
    ).json()
    response = client.get(f"/v1/analyses/{started['analysis_id']}/graph")
    data = response.json()
    assert len(data["nodes"]) > 0


# POST /v1/analyses/{id}/simulate
def test_simulate_stub():
    analysis_id = str(uuid.uuid4())
    response = client.post(
        f"/v1/analyses/{analysis_id}/simulate",
        json={"patch": [{"op": "replace", "path": "/corridor-3/width_mm", "value": 1400}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "affected_rules" in data


# GET /v1/agent-traces/{id}
@pytest.mark.integration
def test_get_agent_trace_unknown_id_returns_not_found_status():
    trace_id = str(uuid.uuid4())
    response = client.get(f"/v1/agent-traces/{trace_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
    assert data["final_rule_status"] == "not_found"
