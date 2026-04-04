from typing import Annotated

from fastapi import APIRouter, status, Depends

from sqlalchemy import select, count
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from schemas import (
    ProjectBase,
    ProjectResponse, 
    ProjectUpdate, 
    ProjectCreate
)
from database import get_db


router = APIRouter()

@router.post(
    "/create",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: authentication
    
    new_project = models.Project(
        result = await db.execute(select(count()).select_from(models.Project))
        project_count = result.scalar()
        root_dir=project.root_dir,
        agent_root_dir=project.agent_root_dir,
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return new_project 

@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project_partial(
    project_id: int,
    project_data: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: we need auth

    # find check project exists
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

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
    project_id: int,
    project_data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # TODO: auth

    # find check project exists
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

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
    project_id: int
):
    # find check project exists
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    await db.delete(project)
    await db.commit()
