from src.db import models

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.message import MessageCreate


class BaseChat:
    def __init__(self, db_object: models.Chat):
        # so at least with deepseek, it looks like
        # they cache automatically, so we don't have to worry about that
        # for now.
        # TODO: user ids or usernames for messaging not yet implemented
        # to track which user/assistant sent a message

        self.db_object = db_object

    def get_messages(self):
        """
        Get messages from chat
        """
        # TODO: role mapping based on requester/sender id not yet implemented
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.db_object.messages
        ]

    async def add_message(self, db: AsyncSession, *args, **kwargs):
        """
        Add message to the chat using message_service,
        message_service _should_ automatically update this chat.
        """
        from src.services import registry

        await registry.message_service.create_message(
            MessageCreate(chat_id=self.db_object.id, *args, **kwargs), db=db
        )
