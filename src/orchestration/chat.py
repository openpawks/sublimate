from src.schemas.data import ChatData, MessageData
from src.schemas.message import MessageCreate


class BaseChat:
    def __init__(self, data: ChatData, messages: list[dict] | None = None):
        self._data = data
        self._messages = messages or []

    async def get_messages(self, db=None, *args, **kwargs) -> list[MessageData]:
        from src.db.database import get_db_session
        from src.services.registry import registry

        db = db or await get_db_session()
        self._messages = [
            MessageData.model_validate(msg)
            for msg in await registry.message_service.get_messages_by_chat(
                chat_id=self._data.id, db=db
            )
        ]
        return [msg.model_dump(*args, **kwargs) for msg in self._messages]

    async def add_message(self, db, broadcast: bool = True, *args, **kwargs):
        """
        Add message to the chat using message_service,
        message_service _should_ automatically update this chat.

        Args:
            broadcast: should it broadcast the message
                - ideally only do this for full messages
                - or messages you want the user to see!
        """
        from src.services import registry

        new_message = MessageCreate(chat_id=self._data.id, *args, **kwargs)
        msg = await registry.message_service.create_message(new_message, db=db)
        if msg:
            self._messages.append({"role": msg.role, "content": msg.content})
            await registry.connection_manager.broadcast_message_chat(new_message)
