from src.orchestration.chat import BaseChat
from src.db import models
from src.db.database import get_db_session

from sqlalchemy import select, update, delete


class ChatService:
    def __init__(self):
        self.chats_in_memory = {}

    def get_base_chat_by_id(self, id: int):
        """
        Get BaseChat by id, from memory

        Args:
            id: chat id
        """
        return self.chats_in_memory.get(id)

    def get_base_chat(self, db_object: models.Chat):
        """
        Load BaseChat into memory
        """
        chat = self.chats_in_memory.get(db_object.id)
        if chat:
            return chat

        self.chats_in_memory[db_object.id] = BaseChat(
            db_object=db_object,
        )

        return self.chats_in_memory.get(db_object.id)

    async def get_chat_by_id(self, id: int) -> BaseChat | None:
        """
        Get chat object by id (BaseChat object)

        Args:
            id: chat id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Chat).where(models.Chat.id == id))
        chat_db = result.scalars().first()

        if chat_db:
            return self.get_base_chat(chat_db)
        else:
            return None

    async def get_chats_by_task(self, task_id: int) -> list[BaseChat]:
        """
        Get all chats for a task
        """
        db = await get_db_session()
        result = await db.execute(
            select(models.Chat).where(models.Chat.task_id == task_id)
        )
        chats = result.scalars().all()
        return [self.get_base_chat(chat) for chat in chats]

    async def get_all_chats(self) -> list[BaseChat]:
        """
        Get all chats
        """
        db = await get_db_session()
        result = await db.execute(select(models.Chat))
        chats = result.scalars().all()
        return [self.get_base_chat(chat) for chat in chats]

    async def create_chat_db(
        self,
        task_id: int,
    ):
        """
        Create a new chat in the database

        Args:
            task_id: related task id
        """
        db = await get_db_session()

        new_chat = models.Chat(task_id=task_id)

        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)

        return new_chat

    async def create_chat(self, task_id: int):
        """
        Helper function to create a chat
        """
        chat_obj = await self.create_chat_db(task_id)
        return self.get_base_chat(chat_obj)

    async def update_chat(self, id: int, task_id: int | None = None) -> BaseChat | None:
        """
        Update a chat's task_id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Chat).where(models.Chat.id == id))
        chat_db = result.scalars().first()
        if not chat_db:
            return None

        update_data = {}
        if task_id is not None:
            update_data["task_id"] = task_id

        if update_data:
            await db.execute(
                update(models.Chat).where(models.Chat.id == id).values(**update_data)
            )
            await db.commit()
            await db.refresh(chat_db)
            await db.refresh(self.get_base_chat(chat_db).db_object)

        return self.get_base_chat(chat_db)

    async def delete_chat(self, id: int) -> bool:
        """
        Delete a chat by id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Chat).where(models.Chat.id == id))
        chat_db = result.scalars().first()
        if not chat_db:
            return False

        await db.execute(delete(models.Chat).where(models.Chat.id == id))
        await db.commit()

        if id in self.chats_in_memory:
            del self.chats_in_memory[id]

        return True


chat_service = ChatService()
