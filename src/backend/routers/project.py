from fastapi import APIRouter, HTTPException, status

from ...services.project import project_service
from ...schemas.project import ProjectCreate, ProjectUpdate

router = APIRouter()


def _project_to_dict(project) -> dict:
    d = project._data
    return {
        "id": d.id,
        "name": d.name,
        "user_id": d.user_id,
        "root_dir": d.root_dir,
        "settings_yaml": d.settings_yaml,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
async def get_projects(user_id: int | None = None):
    if user_id is not None:
        projects = await project_service.get_projects_by_user(user_id)
    else:
        projects = await project_service.get_all_projects()
    return [_project_to_dict(p) for p in projects]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(new_project: ProjectCreate):
    project = await project_service.create_project(new_project)
    if not project:
        raise HTTPException(status_code=400, detail="Failed to create project")
    return _project_to_dict(project)


@router.get("/{project_id}")
async def get_project(project_id: int):
    project = await project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_dict(project)


@router.patch("/{project_id}")
async def update_project(project_id: int, project_update: ProjectUpdate):
    project = await project_service.update_project(project_id, project_update)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_dict(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int):
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
