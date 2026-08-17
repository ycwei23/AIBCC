from fastapi import FastAPI

from app.monitoring import log_request_middleware, pipeline_metrics
from app.routers import analyses, projects, rules

app = FastAPI(
    title="AIBCC API",
    description="AI Building Compliance Copilot",
    version="0.1.0",
)

app.middleware("http")(log_request_middleware)

app.include_router(projects.router)
app.include_router(analyses.router)
app.include_router(rules.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/v1/metrics")
def get_metrics():
    return pipeline_metrics.snapshot()
