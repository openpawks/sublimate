from src.services.message import message_service

from src.backend import models


class BaseChat:
    def __init__(self, db_object: models.Chat):
        # so at least with deepseek, it looks like
        # they cache automatically, so we don't have to worry about that
        # for now.
        # TODO: user ids or usernames for messaging
        # to track which user/assistant sent a message

        self.db_object = db_object

    def get_messages(self):
        """
        Get messages from chat
        """
        # TODO: dynamically set role based on requester/sender id, so other's seem to be "user"
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.db_object.messages
        ]

    async def add_message(self, *args, **kwargs):
        """
        Add message to the chat using message_service,
        message_service _should_ automatically update this chat.
        """
        await message_service.create_message(
            *args,
            **kwargs,
        )
