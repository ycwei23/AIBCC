import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# POST /v1/projects
def test_create_project():
    response = client.post("/v1/projects", json={"name": "Test Building", "building_use": "office"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Building"
    assert data["building_use"] == "office"


def test_create_project_name_only():
    response = client.post("/v1/projects", json={"name": "Minimal"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal"
    assert data["building_use"] is None


# POST /v1/projects/{id}/files
def test_upload_file_stub():
    project_id = str(uuid.uuid4())
    response = client.post(
        f"/v1/projects/{project_id}/files",
        files={"file": ("plan.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 202
    data = response.json()
    assert "file_id" in data
    assert data["status"] == "pending"


# POST /v1/projects/{id}/analyses
def test_start_analysis_stub():
    project_id = str(uuid.uuid4())
    response = client.post(f"/v1/projects/{project_id}/analyses")
    assert response.status_code == 202
    data = response.json()
    assert "analysis_id" in data
    assert data["status"] == "uploaded"


# GET /v1/analyses/{id}
def test_get_analysis_stub():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "counts" in data


# GET /v1/analyses/{id}/violations
def test_get_violations_stub():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}/violations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# GET /v1/analyses/{id}/report
def test_get_report_stub():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}/report")
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data


# GET /v1/rules
def test_get_rules_stub():
    response = client.get("/v1/rules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# POST /v1/analyses/{id}/copilot
def test_copilot_stub():
    analysis_id = str(uuid.uuid4())
    response = client.post(
        f"/v1/analyses/{analysis_id}/copilot",
        json={"question": "走道加寬 200mm 後是否合法？"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "trace_id" in data


# GET /v1/analyses/{id}/graph
def test_get_graph_stub():
    analysis_id = str(uuid.uuid4())
    response = client.get(f"/v1/analyses/{analysis_id}/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


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
def test_get_agent_trace_stub():
    trace_id = str(uuid.uuid4())
    response = client.get(f"/v1/agent-traces/{trace_id}")
    assert response.status_code == 200
    data = response.json()
    assert "trace_id" in data
    assert "steps" in data
