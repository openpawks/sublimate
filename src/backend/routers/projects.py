from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    TaskCreate,
    TaskResponse
)
from database import get_db


router = APIRouter()

async def get_project_or_404(
        project_id: int,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: authentication
    
    new_project = models.Project(
        root_dir=project.root_dir,
        agent_root_dir=project.agent_root_dir,
    )

    # so really, we should also have project INIT, which creates heartbeats and stuff for the AI models.
    
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return new_project

@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project_partial(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    project_data: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: we need auth

    # update
    update_data = project_data.model_dump(exclude_unset=True)
    for f,v in update_data.items():
        setattr(project, f, v)

    await db.commit()
    await db.refresh(project)
    return project

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project_full(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    project_data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: auth

    update_data = project_data.model_dump()
    for f,v in update_data.items():
        setattr(project, f, v)

    await db.commit()
    await db.refresh(project)

    return project

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project: Annotated[models.Project, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: authentication

    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def get_tasks(
        project: Annotated[models.Project, Depends(get_project_or_404)],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Task).where(models.Task.project_id == project.id).order_by(models.Task.created_at.desc()))
    tasks = result.scalars().all()

    return tasks

@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_task(
        project: Annotated[models.Project, Depends(get_project_or_404)],
        task: TaskCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    new_task = models.Task(project_id=project.id, chat_id=task.chat_id)

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

@router.get("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
        project: Annotated[models.Project, Depends(get_project_or_404)],
        task_id: int,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Task).where(models.Task.id == task_id, models.Task.project_id == project.id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task

@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
        project: Annotated[models.Project, Depends(get_project_or_404)],
        task_id: int,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Task).where(models.Task.id == task_id, models.Task.project_id == project.id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(task)
    await db.commit()


