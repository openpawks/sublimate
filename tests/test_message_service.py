import pytest
from unittest.mock import patch, AsyncMock
from src.services.message import MessageService
from src.schemas.message import MessageCreate, MessageUpdate
from src.db import models


class TestMessageService:
    """Test suite for MessageService."""

    @pytest.fixture
    def message_service(self):
        """Create a fresh MessageService instance for each test."""
        return MessageService()

    @pytest.mark.asyncio
    async def test_create_message(self, message_service, async_session, test_chat):
        """Test creating a new message."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            # Mock chat_service.get_chat_by_id to return test chat
            mock_chat = AsyncMock()
            mock_chat.db_object = test_chat
            with patch(
                "src.services.chat.chat_service.get_chat_by_id", return_value=mock_chat
            ):
                message_create = MessageCreate(
                    chat_id=test_chat.id, content="Test message content", role="user"
                )

                result = await message_service.create_message(message_create)

                assert result is not None
                assert result.content == "Test message content"
                assert result.role == "user"
                assert result.chat_id == test_chat.id

    @pytest.mark.asyncio
    async def test_create_message_chat_not_found(self, message_service, async_session):
        """Test creating a message for non-existent chat returns None."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            with patch(
                "src.services.chat.chat_service.get_chat_by_id", return_value=None
            ):
                message_create = MessageCreate(
                    chat_id=9999, content="Test content", role="user"
                )

                result = await message_service.create_message(message_create)
                assert result is None

    @pytest.mark.asyncio
    async def test_get_message_by_id(
        self, message_service, async_session, test_message
    ):
        """Test retrieving a message by ID."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            result = await message_service.get_message_by_id(test_message.id)

            assert result is not None
            assert result.id == test_message.id
            assert result.content == test_message.content
            assert result.chat_id == test_message.chat_id

    @pytest.mark.asyncio
    async def test_get_message_by_id_not_found(self, message_service, async_session):
        """Test retrieving a non-existent message returns None."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            result = await message_service.get_message_by_id(9999)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_messages_by_chat(
        self, message_service, async_session, test_chat
    ):
        """Test retrieving all messages for a chat."""
        # Create multiple messages for the chat
        message1 = models.Message(
            content="Message 1", role="user", chat_id=test_chat.id
        )
        message2 = models.Message(
            content="Message 2", role="assistant", chat_id=test_chat.id
        )
        async_session.add_all([message1, message2])
        await async_session.commit()

        with patch("src.services.message.get_db_session", return_value=async_session):
            result = await message_service.get_messages_by_chat(test_chat.id)

            assert len(result) >= 2  # Should have at least the two messages
            contents = [m.content for m in result]
            assert "Message 1" in contents
            assert "Message 2" in contents

    @pytest.mark.asyncio
    async def test_get_all_messages(self, message_service, async_session, test_message):
        """Test retrieving all messages."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            result = await message_service.get_all_messages()

            assert len(result) >= 1
            assert any(m.id == test_message.id for m in result)

    @pytest.mark.asyncio
    async def test_update_message(self, message_service, async_session, test_message):
        """Test updating a message."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            message_update = MessageUpdate(
                chat_id=test_message.chat_id, content="Updated content", role="system"
            )

            result = await message_service.update_message(
                test_message.id, message_update
            )

            assert result is not None
            assert result.content == "Updated content"
            assert result.role == "system"
            assert result.chat_id == test_message.chat_id

    @pytest.mark.asyncio
    async def test_update_message_partial(
        self, message_service, async_session, test_message
    ):
        """Test partially updating a message."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            # Only update the content
            message_update = MessageUpdate(content="Only content updated")

            result = await message_service.update_message(
                test_message.id, message_update
            )

            assert result is not None
            assert result.content == "Only content updated"
            # Other fields should remain unchanged
            assert result.role == test_message.role
            assert result.chat_id == test_message.chat_id

    @pytest.mark.asyncio
    async def test_update_message_not_found(self, message_service, async_session):
        """Test updating a non-existent message returns None."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            message_update = MessageUpdate(content="Nonexistent message")

            result = await message_service.update_message(9999, message_update)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_message(self, message_service, async_session, test_message):
        """Test deleting a message."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            # First verify message exists
            result = await message_service.get_message_by_id(test_message.id)
            assert result is not None

            # Delete the message
            delete_result = await message_service.delete_message(test_message.id)
            assert delete_result is True

            # Verify message no longer exists
            result = await message_service.get_message_by_id(test_message.id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, message_service, async_session):
        """Test deleting a non-existent message returns False."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            result = await message_service.delete_message(9999)
            assert result is False

    @pytest.mark.asyncio
    async def test_message_content_length(
        self, message_service, async_session, test_chat
    ):
        """Test creating messages with different content lengths."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            mock_chat = AsyncMock()
            mock_chat.db_object = test_chat
            with patch(
                "src.services.chat.chat_service.get_chat_by_id", return_value=mock_chat
            ):
                # Short message
                short_msg = MessageCreate(
                    chat_id=test_chat.id, content="Hi", role="user"
                )
                result1 = await message_service.create_message(short_msg)
                assert result1 is not None
                assert result1.content == "Hi"

                # Long message (should still work within schema limits)
                long_content = "A" * 1000
                long_msg = MessageCreate(
                    chat_id=test_chat.id, content=long_content, role="assistant"
                )
                result2 = await message_service.create_message(long_msg)
                assert result2 is not None
                assert len(result2.content) == 1000

    @pytest.mark.asyncio
    async def test_message_role_validation(
        self, message_service, async_session, test_chat
    ):
        """Test creating messages with different roles."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            mock_chat = AsyncMock()
            mock_chat.db_object = test_chat
            with patch(
                "src.services.chat.chat_service.get_chat_by_id", return_value=mock_chat
            ):
                roles = ["user", "assistant", "system", "other"]
                for role in roles:
                    msg = MessageCreate(
                        chat_id=test_chat.id, content=f"Message as {role}", role=role
                    )
                    result = await message_service.create_message(msg)
                    assert result is not None
                    assert result.role == role

    @pytest.mark.asyncio
    async def test_message_created_at(self, message_service, async_session, test_chat):
        """Test that messages have created_at timestamps."""
        with patch("src.services.message.get_db_session", return_value=async_session):
            mock_chat = AsyncMock()
            mock_chat.db_object = test_chat
            with patch(
                "src.services.chat.chat_service.get_chat_by_id", return_value=mock_chat
            ):
                message_create = MessageCreate(
                    chat_id=test_chat.id, content="Timestamp test", role="user"
                )

                result = await message_service.create_message(message_create)

                assert result is not None
                assert hasattr(result, "created_at")
                assert result.created_at is not None
