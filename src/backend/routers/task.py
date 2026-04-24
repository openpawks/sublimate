from fastapi import APIRouter, HTTPException, Depends, status

from ...services.task import task_service
from ...schemas.task import TaskCreate, TaskUpdate

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.db.database import get_db_session

router = APIRouter()


def _task_to_dict(task) -> dict:
    d = task._data
    return {
        "id": d.id,
        "name": d.name,
        "project_id": d.project_id,
        "root_dir": d.root_dir,
        "open": d.open,
        "todos": d.todos,
        "settings_yaml": d.settings_yaml,
        "chat_id": d.chat_id,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
async def get_tasks(project_id: int | None = None):
    if project_id is not None:
        tasks = await task_service.get_tasks_by_project(project_id)
    else:
        tasks = await task_service.get_all_tasks()
    return [_task_to_dict(t) for t in tasks]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    new_task: TaskCreate, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    task = await task_service.create_task(new_task, db)
    if not task:
        raise HTTPException(status_code=400, detail="Failed to create task")
    return _task_to_dict(task)


@router.get("/{task_id}")
async def get_task(task_id: int):
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.patch("/{task_id}")
async def update_task(task_id: int, task_update: TaskUpdate):
    task = await task_service.update_task(task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    deleted = await task_service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
