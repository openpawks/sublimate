from src.schemas.data import ChatData
from src.schemas.message import MessageCreate


class BaseChat:
    def __init__(self, data: ChatData, messages: list[dict] | None = None):
        self._data = data
        self._messages = messages or []

    def get_messages(self):
        """
        Get messages from chat
        """
        return self._messages

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
            registry.connection_manager.broadcast_message_chat(new_message)
