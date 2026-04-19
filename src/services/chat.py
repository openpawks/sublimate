from src.orchestration.chat import BaseChat
from src.db import models
from src.db.database import get_db

from sqlalchemy import select


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

    async def get_chat_by_id(self, id: int) -> BaseChat:
        """
        Get chat object by id (BaseChat object)

        Args:
            id: chat id
        """
        db = await get_db()

        chat_db = await db.execute(select(models.Chat.id == id)).scalars().first()

        if chat_db:
            return self.get_base_chat(chat_db)
        else:
            return None

    async def create_chat_db(
        self,
        task_id: int,
    ):
        """
        Create a new chat in the database

        Args:
            name: related task id
        """
        db = await get_db()

        new_chat = models.Chat(task_id=task_id)

        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)

        return new_chat

    async def create_chat(self, *args, **kwargs):
        """
        Helper function to create a chat
        """
        chat_obj = await self.create_chat_db(*args, **kwargs)
        return await self.get_base_chat(chat_obj)


chat_service = ChatService()
