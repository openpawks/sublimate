from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

import models

from schemas import ProjectCreate, ProjectUpdate


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
