from src.orchestration.task import BaseTask
from src.backend import models
from src.backend.database import get_db

from src.services.project import project_service

from src.schemas.task import TaskCreate

from sqlalchemy import select


class TaskService:
    def __init__(self):
        self.tasks_in_memory = {}

    def get_base_task_by_id(self, id: int):
        """
        Get BaseTask by id, from memory

        Args:
            id: task id
        """
        return self.tasks_in_memory.get(id)

    def get_base_task(self, db_object: models.Task):
        """
        Load BaseTask into memory
        """
        task = self.tasks_in_memory.get(id)
        if task:
            return task

        self.tasks_in_memory[id] = BaseTask(
            db_object=db_object,
        )

        return self.tasks_in_memory.get(id)

    def get_task_by_id(self, id: int) -> BaseTask:
        """
        Get task object by id (BaseTask object)

        Args:
            id: task id
        """
        db = await get_db()

        task_db = await db.execute(select(models.Task.id == id)).scalars().first()

        if task_db:
            return self.get_base_task(task_db)
        else:
            return None

    async def create_task_db(self, task: TaskCreate):
        """
        Create a new task in the database
        """
        db = await get_db()

        project = project_service.get_project_by_id(task.project_id)
        if not project:
            # project doesn't exist
            return

        new_task = models.Task(
            name=task.name,
            project_id=task.project_id,
            root_dir=task.root_dir,
            settings_yaml=task.settings_yaml,
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        await db.refresh(project.db_object)

        return new_task

    async def create_task(self, *args, **kwargs):
        """
        Helper function to create a task
        """
        task_obj = await self.create_task_db(*args, **kwargs)
        return await self.get_base_task(task_obj)


task_service = TaskService()
