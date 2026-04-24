import pytest
from unittest.mock import patch, AsyncMock
from src.services.message import MessageService
from src.schemas.message import MessageCreate


class TestMessageService:
    """Test suite for MessageService."""

    @pytest.fixture
    def message_service(self):
        """Create a fresh MessageService instance for each test."""
        return MessageService()

    @pytest.mark.asyncio
    async def test_create_message(self, message_service, async_session, test_chat):
        """Test creating a new message."""
        # Mock chat_service.get_chat_by_id to return test chat
        mock_chat = AsyncMock()
        mock_chat.db_object = test_chat
        with patch(
            "src.services.chat.chat_service.get_chat_by_id", return_value=mock_chat
        ):
            message_create = MessageCreate(
                chat_id=test_chat.id, content="Test message content", role="user"
            )

            result = await message_service.create_message(message_create, async_session)

            assert result is not None
            assert result.content == "Test message content"
            assert result.role == "user"
            assert result.chat_id == test_chat.id

    @pytest.mark.asyncio
    async def test_create_message_chat_not_found(self, message_service, async_session):
        """Test creating a message for non-existent chat returns None."""
        with patch("src.services.chat.chat_service.get_chat_by_id", return_value=None):
            message_create = MessageCreate(
                chat_id=9999, content="Test content", role="user"
            )
