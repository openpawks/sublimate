from fastapi import APIRouter, HTTPException, status

from ...services.task import task_service
from ...schemas.task import TaskCreate, TaskUpdate

router = APIRouter()


def _task_to_dict(task) -> dict:
    db = task.db_object
    return {
        "id": db.id,
        "name": db.name,
        "project_id": db.project_id,
        "root_dir": db.root_dir,
        "open": db.open,
        "todos": db.todos,
        "settings_yaml": db.settings_yaml,
        "chat_id": db.chat_id,
        "created_at": db.created_at.isoformat() if db.created_at else None,
    }


@router.get("")
async def get_tasks(project_id: int | None = None):
    if project_id is not None:
        tasks = await task_service.get_tasks_by_project(project_id)
    else:
        tasks = await task_service.get_all_tasks()
    return [_task_to_dict(t) for t in tasks]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(new_task: TaskCreate):
    task = await task_service.create_task(new_task)
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
