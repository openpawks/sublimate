from src.db import models

from src.schemas.message import MessageCreate, MessageUpdate

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, update, delete


class MessageService:
    def __init__(self):
        pass

    async def create_message(self, message: MessageCreate, db: AsyncSession):
        from src.services import registry

        chat = await registry.chat_service.get_chat_by_id(message.chat_id, db)

        if not chat:
            return None

        message_obj = models.Message(
            content=message.content, role=message.role, chat_id=message.chat_id
        )

        db.add(message_obj)
        await db.commit()
        await db.refresh(message_obj)

        return message_obj

    async def get_message_by_id(self, id: int, db: AsyncSession):
        result = await db.execute(select(models.Message).where(models.Message.id == id))
        message = result.scalars().first()
        return message

    async def get_messages_by_chat(self, chat_id: int, db: AsyncSession):
        result = await db.execute(
            select(models.Message).where(models.Message.chat_id == chat_id)
        )
        messages = result.scalars().all()
        return messages

    async def get_all_messages(self, db: AsyncSession):
        result = await db.execute(select(models.Message))
        messages = result.scalars().all()
        return messages

    async def update_message(
        self, id: int, message_update: MessageUpdate, db: AsyncSession
    ):
        result = await db.execute(select(models.Message).where(models.Message.id == id))
        message = result.scalars().first()
        if not message:
            return None

        update_data = message_update.model_dump(exclude_unset=True)

        if update_data:
            await db.execute(
                update(models.Message)
                .where(models.Message.id == id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(message)

        return message

    async def delete_message(self, id: int, db: AsyncSession) -> bool:
        result = await db.execute(select(models.Message).where(models.Message.id == id))
        message = result.scalars().first()
        if not message:
            return False

        await db.execute(delete(models.Message).where(models.Message.id == id))
        await db.commit()
        return True


message_service = MessageService()
