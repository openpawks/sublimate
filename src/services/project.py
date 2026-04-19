from src.orchestration.project import BaseProject
from src.db import models
from src.db.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.project import ProjectCreate, ProjectUpdate

from sqlalchemy import select, update, delete


class ProjectService:
    def __init__(self):
        self.projects_in_memory = {}

    def get_base_project_by_id(self, id: int):
        """
        Get project by id (from memory), just the BaseProject object

        Args:
            id: project id
        """
        return self.projects_in_memory.get(id)

    def get_base_project(self, db_object: models.Project):
        """
        Load BaseProject into memory
        """
        project = self.projects_in_memory.get(db_object.id)
        if project:
            return project

        self.projects_in_memory[db_object.id] = BaseProject(db_object=db_object)

        return self.projects_in_memory.get(db_object.id)

    async def get_project_by_id(
        self, id: int, db: AsyncSession | None = None
    ) -> BaseProject | None:
        """
        Get project by id, (BaseProject object)

        Args:
            id: project id
            db: optional database session (creates one if not provided)
        """
        close_db = False
        if db is None:
            db = await get_db_session()
            close_db = True

        try:
            result = await db.execute(
                select(models.Project).where(models.Project.id == id)
            )
            project_db = result.scalars().first()

            if project_db:
                return self.get_base_project(project_db)
            else:
                return None
        finally:
            if close_db:
                await db.close()

    async def get_projects_by_user(
        self, user_id: int, db: AsyncSession | None = None
    ) -> list[BaseProject]:
        """
        Get all projects for a user
        """
        close_db = False
        if db is None:
            db = await get_db_session()
            close_db = True

        try:
            result = await db.execute(
                select(models.Project).where(models.Project.user_id == user_id)
            )
            projects = result.scalars().all()
            return [self.get_base_project(project) for project in projects]
        finally:
            if close_db:
                await db.close()

    async def get_all_projects(self) -> list[BaseProject]:
        """
        Get all projects
        """
        db = await get_db_session()
        result = await db.execute(select(models.Project))
        projects = result.scalars().all()
        return [self.get_base_project(project) for project in projects]

    async def create_project_db(
        self,
        project: ProjectCreate,
    ):
        """
        Create a new project in the database
        """
        db = await get_db_session()

        new_project = models.Project(
            name=project.name,
            user_id=project.user_id,
            root_dir=project.root_dir,
            settings_yaml=project.settings_yaml or "",
        )

        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)

        return new_project

    async def create_project(self, project: ProjectCreate):
        """
        Helper function to create a project
        """
        project_obj = await self.create_project_db(project)
        return self.get_base_project(project_obj)

    async def update_project(
        self, id: int, project_update: ProjectUpdate
    ) -> BaseProject | None:
        """
        Update an existing project
        """
        db = await get_db_session()

        result = await db.execute(select(models.Project).where(models.Project.id == id))
        project_db = result.scalars().first()
        if not project_db:
            return None

        update_data = project_update.model_dump(exclude_unset=True)

        if update_data:
            await db.execute(
                update(models.Project)
                .where(models.Project.id == id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(project_db)

        return self.get_base_project(project_db)

    async def delete_project(self, id: int) -> bool:
        """
        Delete a project by id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Project).where(models.Project.id == id))
        project_db = result.scalars().first()
        if not project_db:
            return False

        await db.execute(delete(models.Project).where(models.Project.id == id))
        await db.commit()

        if id in self.projects_in_memory:
            del self.projects_in_memory[id]

        return True


project_service = ProjectService()
