from src.backend import models
from src.backend.database import get_db

from src.schemas.message import MessageCreate

from src.services import chat_service


class MessageService:
    def __init__(self):
        pass

    async def create_message(self, message: MessageCreate):
        """
        Create a message for a given chat_id
        Also attempt to update the chat object in memory's data
        """
        db = await get_db()

        chat = chat_service.get_chat_by_id(message.chat_id)

        if not chat:
            return

        message_obj = models.Message(
            content=message.content, role=message.role, chat_id=message.chat_id
        )

        db.add(message_obj)
        await db.commit()
        await db.refresh(message_obj)
        await db.refresh(chat.db_object)

        return message_obj


message_service = MessageService()
