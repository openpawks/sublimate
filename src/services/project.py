from src.orchestration.project import BaseProject
from src.backend import models
from src.backend.database import get_db

from src.schemas.project import ProjectCreate

from sqlalchemy import select


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

    def get_mem_project(self, db_object: models.Project):
        """
        Load BaseProject into memory
        """
        project = self.projects_in_memory.get(id)
        if project:
            return project

        self.projects_in_memory[id] = BaseProject(db_object=db_object)

        return self.projects_in_memory.get(id)

    async def get_project_by_id(self, id: int) -> BaseProject:
        """
        Get project by id, (BaseProject object)

        Args:
            id: project id
        """
        db = await get_db()

        project_db = await db.execute(select(models.Project.id == id)).scalars().first()

        if project_db:
            return self.get_mem_project(project_db)
        else:
            return None

    async def create_project_db(
        self,
        project: ProjectCreate,
    ):
        """
        Create a new project in the database
        """
        db = await get_db()

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

    def create_project(self, *args, **kwargs):
        """
        Helper function to create a project
        """
        project_obj = await self.create_project_db(*args, **kwargs)
        return await self.get_base_project(project_obj)


project_service = ProjectService()
