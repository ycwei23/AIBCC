from app.monitoring import PipelineMetrics


def test_metrics_start_at_zero():
    metrics = PipelineMetrics()
    assert metrics.snapshot() == {"success_count": 0, "failure_count": 0, "by_status": {}}


def test_record_success_increments_counter():
    metrics = PipelineMetrics()
    metrics.record_status("completed")
    snapshot = metrics.snapshot()
    assert snapshot["success_count"] == 1
    assert snapshot["by_status"]["completed"] == 1


def test_record_failed_increments_failure_counter():
    metrics = PipelineMetrics()
    metrics.record_status("failed")
    snapshot = metrics.snapshot()
    assert snapshot["failure_count"] == 1


def test_metrics_endpoint_returns_snapshot():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/v1/metrics")
    assert response.status_code == 200
    assert "success_count" in response.json()
