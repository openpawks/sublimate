from src.orchestration.chat import BaseChat
from src.db import models
from src.schemas.data import ChatData

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    def __init__(self):
        self.chats_in_memory = {}

    def get_base_chat_by_id(self, id: int):
        return self.chats_in_memory.get(id)

    def get_or_create_base_chat(
        self, data: ChatData, messages: list[dict] | None = None
    ):
        chat = self.chats_in_memory.get(data.id)
        if chat:
            return chat

        self.chats_in_memory[data.id] = BaseChat(
            data=data,
            messages=messages,
        )

        return self.chats_in_memory.get(data.id)

    async def get_chat_by_id(self, id: int, db: AsyncSession) -> BaseChat | None:
        result = await db.execute(
            select(models.Chat)
            .where(models.Chat.id == id)
            .options(selectinload(models.Chat.messages))
        )
        chat_db = result.scalars().first()

        if chat_db:
            data = ChatData.model_validate(chat_db)
            messages = [
                {"role": m.role, "content": m.content} for m in chat_db.messages
            ]
            return self.get_or_create_base_chat(data, messages)
        else:
            return None

    async def get_chats_by_task(self, task_id: int, db: AsyncSession) -> list[BaseChat]:
        result = await db.execute(
            select(models.Chat)
            .where(models.Chat.task_id == task_id)
            .options(selectinload(models.Chat.messages))
        )
        chats = result.scalars().all()
        return [
            self.get_or_create_base_chat(
                ChatData.model_validate(c),
                [{"role": m.role, "content": m.content} for m in c.messages],
            )
            for c in chats
        ]

    async def get_all_chats(self, db: AsyncSession) -> list[BaseChat]:
        result = await db.execute(
            select(models.Chat).options(selectinload(models.Chat.messages))
        )
        chats = result.scalars().all()
        return [
            self.get_or_create_base_chat(
                ChatData.model_validate(c),
                [{"role": m.role, "content": m.content} for m in c.messages],
            )
            for c in chats
        ]

    async def create_chat_db(self, task_id: int, db: AsyncSession):
        new_chat = models.Chat(task_id=task_id)

        db.add(new_chat)
        await db.flush()
        await db.refresh(new_chat)

        return new_chat

    async def create_chat(self, task_id: int, db: AsyncSession):
        chat_obj = await self.create_chat_db(task_id, db)
        data = ChatData.model_validate(chat_obj)
        return self.get_or_create_base_chat(data, messages=[])

    async def update_chat(
        self, id: int, db: AsyncSession, task_id: int | None = None
    ) -> BaseChat | None:
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

        chat = self.get_base_chat_by_id(id)
        if chat:
            chat._data = ChatData.model_validate(chat_db)

        return self.get_base_chat_by_id(id) or self.get_or_create_base_chat(
            ChatData.model_validate(chat_db)
        )

    async def delete_chat(self, id: int, db: AsyncSession) -> bool:
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
