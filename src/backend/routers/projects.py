from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    TaskCreate,
    TaskResponse,
)
from database import get_db

from services import ProjectService

router = APIRouter()


async def get_project_or_404(
    project_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Project).where(models.Project.id == project_id)
    )
    project = result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return project


@router.get("", response_model=list[ProjectResponse])
async def get_projects(
    db: Annotated[AsyncSession, Depends(get_db)], project_service: ProjectService
):
    return project_service.get_projects(db)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.create_project(project, db)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project_partial(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    project_updated: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.update_project_partial(project, project_updated, db)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project_full(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    project_updated: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.update_project_full(project, project_updated, db)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.delete_project(project, db)


# TASKS


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def get_tasks(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.get_tasks(project, db)


@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_task(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    task: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.create_task(project, task, db)


# maybe change this to /tasks/{task_id}?
@router.get("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.get_task(project, task_id, db)


@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_service: ProjectService,
):
    return project_service.delete_task(project, task_id, db)
