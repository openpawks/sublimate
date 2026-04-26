import asyncio

from src.db import models

from src.schemas.message import MessageCreate, MessageUpdate

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, update, delete


class MessageService:
    def __init__(self):
        pass

    async def create_message(
        self, message: MessageCreate, db: AsyncSession, auto_commit: bool = True
    ):
        from src.services import registry

        chat = await registry.chat_service.get_chat_by_id(message.chat_id, db)

        if not chat:
            return None

        message_obj = models.Message(
            content=message.content, role=message.role, chat_id=message.chat_id
        )

        db.add(message_obj)
        if auto_commit:
            await db.commit()
            await db.refresh(message_obj)
            # TODO: optimise this, create a "broadcast_messages_chat" function in connection manager
            await registry.connection_manager.broadcast_message_chat(message)

        return message_obj

    async def create_messages(
        self,
        messages: list[MessageCreate],
        db: AsyncSession,
        auto_commit: bool = True,
    ):
        from src.services import registry

        if len(messages) <= 0:
            return []

        chat_id = messages[0].chat_id
        if not all([message.chat_id == chat_id for message in messages]):
            # NOTE: just sort by chat id, and do a big for loop around all this to avoid fetching the chat everytime
            raise ValueError(
                "Currently, at the minute, all the chat_id's have to be the same"
            )

        chat = await registry.chat_service.get_chat_by_id(chat_id, db)

        if not chat:
            return None

        message_objects = [
            models.Message(
                content=message.content, role=message.role, chat_id=message.chat_id
            )
            for message in messages
        ]

        for message_obj in message_objects:
            db.add(message_obj)

        if auto_commit:
            await db.commit()
            message_objects = await asyncio.gather(
                *[
                    asyncio.create_task(db.refresh(message_obj))
                    for message_obj in message_objects
                ]
            )
            # TODO: optimise this, create a "broadcast_messages_chat" function in connection manager
            for message in messages:
                await registry.connection_manager.broadcast_message_chat(message)

        return message_objects

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
