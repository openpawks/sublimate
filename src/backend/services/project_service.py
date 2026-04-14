from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

import models

from schemas import ProjectCreate, ProjectUpdate, TaskCreate


class ProjectService:
    def __init__(self, daemon_service):
        self.daemon_service = daemon_service

    async def get_projects(db: AsyncSession):
        result = await db.execute(
            select(models.Project).order_by(models.Project.created_at)
        )
        projects = result.scalars().all()
        return projects

    async def create_project(project: ProjectCreate, db: AsyncSession):
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

    async def update_project_partial(
        project: models.Project, project_updated: ProjectUpdate, db: AsyncSession
    ):
        # TODO: we need auth

        # update
        update_data = project_updated.model_dump(exclude_unset=True)
        for f, v in update_data.items():
            setattr(project, f, v)

        await db.commit()
        await db.refresh(project)
        return project

    async def update_project_full(
        project: models.Project, project_updated: ProjectCreate, db: AsyncSession
    ):
        # TODO: auth

        update_data = project_updated.model_dump()
        for f, v in update_data.items():
            setattr(project, f, v)

        await db.commit()
        await db.refresh(project)

        return project

    async def delete_project(project: models.Project, db: AsyncSession):
        # TODO: authentication

        await db.delete(project)
        await db.commit()

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
