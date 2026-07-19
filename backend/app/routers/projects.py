import uuid
from typing import Optional

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/v1/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    building_use: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    building_use: Optional[str]


@router.post("", status_code=201, response_model=ProjectResponse)
def create_project(body: ProjectCreate):
    return ProjectResponse(
        id=str(uuid.uuid4()),
        name=body.name,
        building_use=body.building_use,
    )


@router.post("/{project_id}/files", status_code=202)
def upload_file(project_id: str, file: UploadFile = File(...)):
    return {"file_id": str(uuid.uuid4()), "status": "pending"}


@router.post("/{project_id}/analyses", status_code=202)
def start_analysis(project_id: str):
    return {"analysis_id": str(uuid.uuid4()), "status": "uploaded"}
