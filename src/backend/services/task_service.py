from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

import models

from schemas import TaskCreate


class TaskService:
    async def get_tasks(project: models.Project, db: AsyncSession):
        result = await db.execute(
            select(models.Task)
            .where(models.Task.project_id == project.id)
            .order_by(models.Task.created_at.desc())
        )
        tasks = result.scalars().all()

        return tasks

    async def create_task(project: models.Project, task: TaskCreate, db: AsyncSession):
        new_task = models.Task(project_id=project.id, chat_id=task.chat_id)

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        return new_task

    async def get_task(project: models.Project, task_id: int, db: AsyncSession):
        result = await db.execute(
            select(models.Task).where(
                models.Task.id == task_id, models.Task.project_id == project.id
            )
        )
        task = result.scalars().first()

        if not task:
            raise ValueError("Task not found")

        return task

    async def delete_task(project: models.Project, task_id: int, db: AsyncSession):
        result = await db.execute(
            select(models.Task).where(
                models.Task.id == task_id, models.Task.project_id == project.id
            )
        )
        task = result.scalars().first()

        if not task:
            raise ValueError("Task not found")

        await db.delete(task)
        await db.commit()
