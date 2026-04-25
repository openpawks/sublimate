from src.orchestration.task import BaseTask
from src.db import models
from src.db.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.task import TaskCreate, TaskUpdate
from src.schemas.data import TaskData, ProjectData, ChatData, is_filesafe

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload


class TaskService:
    def __init__(self):
        self.tasks_in_memory = {}

    def get_base_task_by_id(self, id: int):
        return self.tasks_in_memory.get(id)

    def get_or_create_base_task(self, data: TaskData, project=None, chat=None):
        task = self.tasks_in_memory.get(data.id)
        if task:
            return task

        self.tasks_in_memory[data.id] = BaseTask(
            data=data,
            project=project,
            chat=chat,
        )

        return self.tasks_in_memory.get(data.id)

    async def get_task_by_id(self, id: int) -> BaseTask | None:
        db = await get_db_session()

        result = await db.execute(
            select(models.Task)
            .where(models.Task.id == id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        task_db = result.scalars().first()

        if task_db:
            return self._build_base_task(task_db, db)
        else:
            return None

    async def get_tasks_by_project(self, project_id: int) -> list[BaseTask]:
        db = await get_db_session()
        result = await db.execute(
            select(models.Task)
            .where(models.Task.project_id == project_id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        tasks = result.scalars().all()
        return [self._build_base_task(task, db) for task in tasks]

    async def get_all_tasks(self) -> list[BaseTask]:
        db = await get_db_session()
        result = await db.execute(
            select(models.Task).options(
                selectinload(models.Task.project), selectinload(models.Task.chat)
            )
        )
        tasks = result.scalars().all()
        return [self._build_base_task(task, db) for task in tasks]

    def _build_base_task(self, task_db: models.Task, db) -> BaseTask:
        from src.services import registry

        task_data = TaskData.model_validate(task_db)
        chat_data = ChatData.model_validate(task_db.chat) if task_db.chat else None

        project = None
        if task_db.project:
            project = registry.project_service.get_or_create_base_project(
                ProjectData.model_validate(task_db.project)
            )

        chat = None
        if chat_data:
            chat = registry.chat_service.get_or_create_base_chat(chat_data)

        return self.get_or_create_base_task(data=task_data, project=project, chat=chat)

    async def create_task_db(self, task: TaskCreate, db: AsyncSession):
        from src.services import registry

        project = await registry.project_service.get_project_by_id(task.project_id, db)
        if not project:
            return None

        if not is_filesafe(task.name):
            raise ValueError(
                f"Task name '{task.name}' is not filesafe. Only alphanumeric, underscores, hyphens, and dots allowed."
            )

        # TODO: if parent project has task under same name, not allow
        # WARNING: VERY IMPORTANT

        new_task = models.Task(
            name=task.name,
            project_id=task.project_id,
            root_dir=task.root_dir,
            settings_yaml=task.settings_yaml,
            todos=task.todos or "",
        )

        db.add(new_task)
        await db.flush()

        chat = await registry.chat_service.create_chat(task_id=new_task.id, db=db)
        new_task.chat_id = chat._data.id

        for i in range(0, len(task.goal), 4096):
            await chat.add_message(db=db, role="user", content=task.goal[i : i + 4096])

        await db.commit()

        result = await db.execute(
            select(models.Task)
            .where(models.Task.id == new_task.id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        task_with_relations = result.scalars().first()

        return task_with_relations

    async def create_task(self, task: TaskCreate, db: AsyncSession):
        task_obj = await self.create_task_db(task, db)
        if task_obj:
            task = self._build_base_task(task_obj, db)
            task.chat.add_message(
                db=db, role="system", content=task.tree(), username="system"
            )
            return task
        return None

    async def update_task(self, id: int, task_update: TaskUpdate) -> BaseTask | None:
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

        task = self.get_base_task_by_id(id)
        if task:
            task._data = TaskData.model_validate(task_db)
            return task

        # Re-fetch with relationships to build full BaseTask
        result = await db.execute(
            select(models.Task)
            .where(models.Task.id == id)
            .options(selectinload(models.Task.project), selectinload(models.Task.chat))
        )
        task_db = result.scalars().first()
        return self._build_base_task(task_db, db)

    async def delete_task(self, id: int) -> bool:
        db = await get_db_session()

        result = await db.execute(
            select(models.Task)
            .where(models.Task.id == id)
            .options(selectinload(models.Task.chat))
        )
        task_db = result.scalars().first()
        if not task_db:
            return False

        if task_db.chat:
            task_db.chat.task_id = None
            await db.flush()
            await db.delete(task_db.chat)
            task_db.chat_id = None
            await db.flush()

        await db.execute(delete(models.Task).where(models.Task.id == id))
        await db.commit()

        if id in self.tasks_in_memory:
            del self.tasks_in_memory[id]

        return True


task_service = TaskService()
