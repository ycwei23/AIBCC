from typing import Optional

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.db import analysis_repo
from app.db.session import engine
from app.pipeline.run_analysis import run_analysis

router = APIRouter(prefix="/v1/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    building_use: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    building_use: Optional[str]


class AnalysisStart(BaseModel):
    fixture_key: str = "case_10_empty"


@router.post("", status_code=201, response_model=ProjectResponse)
def create_project(body: ProjectCreate):
    project_id = analysis_repo.create_project(engine, body.name, body.building_use)
    return ProjectResponse(id=project_id, name=body.name, building_use=body.building_use)


@router.post("/{project_id}/files", status_code=202)
def upload_file(project_id: str, file: UploadFile = File(...)):
    file_id = analysis_repo.create_file(engine, project_id, storage_path=file.filename or "unknown", format="pdf")
    return {"file_id": file_id, "status": "pending"}


@router.post("/{project_id}/analyses", status_code=202)
def start_analysis(project_id: str, body: AnalysisStart):
    analysis_id = analysis_repo.create_analysis_run(engine, project_id, None)
    run_analysis(engine, analysis_id, body.fixture_key)
    row = analysis_repo.get_analysis_run(engine, analysis_id)
    return {"analysis_id": analysis_id, "status": row["status"]}
