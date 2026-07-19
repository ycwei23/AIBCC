from fastapi import FastAPI

app = FastAPI(
    title="AIBCC API",
    description="AI Building Compliance Copilot",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
