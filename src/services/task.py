from src.orchestration.task import BaseTask
from src.backend import models
from src.backend.database import get_db

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

    async def create_task_db(
        self,
        name: str,
        project_id: int,
        root_dir: str,
        settings_yaml: str = "",
    ):
        """
        Create a new task in the database

        Args:
            name: name of the task
            project_id: id of parent project
            root_dir: worktree root directory
            settings_yaml: optional extra settings
        """
        db = await get_db()

        new_task = models.Task(
            name=name,
            project_id=project_id,
            root_dir=root_dir,
            settings_yaml=settings_yaml,
        )

        db.add(new_task)
        await db.commit()
        await db.refresh()

        return new_task

    async def create_task(self, *args, **kwargs):
        """
        Helper function to create a task
        """
        task_obj = await self.create_task_db(*args, **kwargs)
        return await self.get_base_task(task_obj)


task_service = TaskService()
