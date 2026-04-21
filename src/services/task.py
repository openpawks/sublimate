from src.orchestration.task import BaseTask
from src.db import models
from src.db.database import get_db_session


from src.schemas.task import TaskCreate, TaskUpdate

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload


class TaskService:
    def __init__(self):
        self.tasks_in_memory = {}

    @staticmethod
    def _is_filesafe(name: str) -> bool:
        """
        Check if a string is safe for use as a filename/branch name.
        Allows alphanumeric, hyphens, underscores, dots, no spaces or slashes.
        """
        import re

        # Allow alphanumeric, hyphen, underscore, dot
        pattern = r"^[a-zA-Z0-9_.-]+$"
        return bool(re.match(pattern, name))

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
        task = self.tasks_in_memory.get(db_object.id)
        if task:
            return task

        self.tasks_in_memory[db_object.id] = BaseTask(
            db_object=db_object,
        )

        return self.tasks_in_memory.get(db_object.id)

    async def get_task_by_id(self, id: int) -> BaseTask | None:
        """
        Get task object by id (BaseTask object)

        Args:
            id: task id
        """
        db = await get_db_session()

        result = await db.execute(
            select(models.Task)
            .where(models.Task.id == id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        task_db = result.scalars().first()

        if task_db:
            return self.get_base_task(task_db)
        else:
            return None

    async def get_tasks_by_project(self, project_id: int) -> list[BaseTask]:
        """
        Get all tasks for a project
        """
        db = await get_db_session()
        result = await db.execute(
            select(models.Task)
            .where(models.Task.project_id == project_id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        tasks = result.scalars().all()
        return [self.get_base_task(task) for task in tasks]

    async def get_all_tasks(self) -> list[BaseTask]:
        """
        Get all tasks
        """
        db = await get_db_session()
        result = await db.execute(
            select(models.Task).options(
                selectinload(models.Task.project), selectinload(models.Task.chat)
            )
        )
        tasks = result.scalars().all()
        return [self.get_base_task(task) for task in tasks]

    async def create_task_db(self, task: TaskCreate):
        """
        Create a new task in the database
        """
        from src.services.project import project_service
        from src.services.chat import chat_service

        db = await get_db_session()

        project = await project_service.get_project_by_id(task.project_id)
        if not project:
            # project doesn't exist
            return None

        if not self._is_filesafe(task.name):
            raise ValueError(
                f"Task name '{task.name}' is not filesafe. Only alphanumeric, underscores, hyphens, and dots allowed."
            )

        new_task = models.Task(
            name=task.name,
            project_id=task.project_id,
            root_dir=task.root_dir,
            settings_yaml=task.settings_yaml,
            todos=task.todos or "",
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        await db.refresh(project.db_object)

        # Create a chat for the task
        chat = await chat_service.create_chat(task_id=new_task.id)
        new_task.chat_id = chat.db_object.id

        # create a message within that new chat
        for i in range(0, len(task.goal), 4096):
            await chat.add_message(role="user", content=task.goal[i : i + 4096])

        await db.commit()

        # Reload task with relationships
        result = await db.execute(
            select(models.Task)
            .where(models.Task.id == new_task.id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        task_with_relations = result.scalars().first()

        return task_with_relations

    async def create_task(self, task: TaskCreate):
        """
        Helper function to create a task
        """
        task_obj = await self.create_task_db(task)
        if task_obj:
            return self.get_base_task(task_obj)
        return None

    async def update_task(self, id: int, task_update: TaskUpdate) -> BaseTask | None:
        """
        Update an existing task
        """
        db = await get_db_session()

        result = await db.execute(select(models.Task).where(models.Task.id == id))
        task_db = result.scalars().first()
        if not task_db:
            return None

        update_data = task_update.model_dump(exclude_unset=True)

        if update_data:
            await db.execute(
                update(models.Task).where(models.Task.id == id).values(**update_data)
            )
            await db.commit()
            await db.refresh(task_db)

        return self.get_base_task(task_db)

    async def delete_task(self, id: int) -> bool:
        """
        Delete a task by id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Task).where(models.Task.id == id))
        task_db = result.scalars().first()
        if not task_db:
            return False

        await db.execute(delete(models.Task).where(models.Task.id == id))
        await db.commit()

        if id in self.tasks_in_memory:
            del self.tasks_in_memory[id]

        return True


task_service = TaskService()
