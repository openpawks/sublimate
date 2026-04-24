import pytest
from src.services.chat import ChatService
from src.db import models


class TestChatService:
    """Test suite for ChatService."""

    @pytest.fixture
    def chat_service(self):
        """Create a fresh ChatService instance for each test."""
        return ChatService()

    @pytest.mark.asyncio
    async def test_create_chat(self, chat_service, async_session, test_project):
        """Test creating a new chat."""
        # First create a task for the chat
        task = models.Task(
            name="chat-task",
            project_id=test_project.id,
            root_dir="/tmp/chat_task",
            settings_yaml="task: settings",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        result = await chat_service.create_chat(task.id, async_session)

        assert result is not None
        assert result.db_object.task_id == task.id

    @pytest.mark.asyncio
    async def test_get_chat_by_id(self, chat_service, async_session, test_chat):
        """Test retrieving a chat by ID."""
        result = await chat_service.get_chat_by_id(test_chat.id, async_session)

        assert result is not None
        assert result.db_object.id == test_chat.id
        assert result.db_object.task_id == test_chat.task_id

    @pytest.mark.asyncio
    async def test_get_chat_by_id_not_found(self, chat_service, async_session):
        """Test retrieving a non-existent chat returns None."""
        result = await chat_service.get_chat_by_id(9999, async_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_chats_by_task(self, chat_service, async_session, test_project):
        """Test retrieving all chats for a task."""
        # Create a task with multiple chats (though typically one chat per task)
        task = models.Task(
            name="multi-chat-task",
            project_id=test_project.id,
            root_dir="/tmp/multi_chat_task",
            settings_yaml="task: settings",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        # Create multiple chats for the same task (unusual but testable)
        chat1 = models.Chat(task_id=task.id)
        chat2 = models.Chat(task_id=task.id)
        async_session.add_all([chat1, chat2])
        await async_session.commit()

        result = await chat_service.get_chats_by_task(task.id, async_session)

        assert len(result) == 2
        chat_ids = [c.db_object.id for c in result]
        assert chat1.id in chat_ids
        assert chat2.id in chat_ids

    @pytest.mark.asyncio
    async def test_get_all_chats(self, chat_service, async_session, test_chat):
        """Test retrieving all chats."""
        result = await chat_service.get_all_chats(async_session)

        assert len(result) >= 1
        assert any(c.db_object.id == test_chat.id for c in result)

    @pytest.mark.asyncio
    async def test_update_chat(self, chat_service, async_session, test_project):
        """Test updating a chat's task_id."""
        # Create original task and chat
        original_task = models.Task(
            name="original-task",
            project_id=test_project.id,
            root_dir="/tmp/original_task",
            settings_yaml="original: settings",
        )
        async_session.add(original_task)
        await async_session.commit()
        await async_session.refresh(original_task)

        chat = models.Chat(task_id=original_task.id)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)

        # Create new task to reassign chat to
        new_task = models.Task(
            name="new-task",
            project_id=test_project.id,
            root_dir="/tmp/new_task",
            settings_yaml="new: settings",
        )
        async_session.add(new_task)
        await async_session.commit()
        await async_session.refresh(new_task)

        result = await chat_service.update_chat(chat.id, async_session, new_task.id)

        assert result is not None
        assert result.db_object.task_id == new_task.id

    @pytest.mark.asyncio
    async def test_update_chat_no_change(self, chat_service, async_session, test_chat):
        """Test updating a chat with None (no change)."""
        original_task_id = test_chat.task_id

        # Update with None should not change anything
        result = await chat_service.update_chat(test_chat.id, async_session, None)

        assert result is not None
        assert result.db_object.task_id == original_task_id

    @pytest.mark.asyncio
    async def test_update_chat_not_found(self, chat_service, async_session):
        """Test updating a non-existent chat returns None."""
        result = await chat_service.update_chat(9999, async_session, 123)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_chat(self, chat_service, async_session, test_chat):
        """Test deleting a chat."""
        # First verify chat exists
        result = await chat_service.get_chat_by_id(test_chat.id, async_session)
        assert result is not None

        # Delete the chat
        delete_result = await chat_service.delete_chat(test_chat.id, async_session)
        assert delete_result is True

        # Verify chat no longer exists
        result = await chat_service.get_chat_by_id(test_chat.id, async_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_chat_not_found(self, chat_service, async_session):
        """Test deleting a non-existent chat returns False."""
        result = await chat_service.delete_chat(9999, async_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_base_chat_by_id(self, chat_service, test_chat):
        """Test getting chat from memory cache."""
        # First add chat to memory
        chat_service.chats_in_memory[test_chat.id] = "mock_chat_object"

        result = chat_service.get_base_chat_by_id(test_chat.id)
        assert result == "mock_chat_object"

    @pytest.mark.asyncio
    async def test_get_base_chat_by_id_not_found(self, chat_service):
        """Test getting non-existent chat from memory returns None."""
        result = chat_service.get_base_chat_by_id(9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_chat_memory_cache(self, chat_service, async_session, test_chat):
        """Test that chats are cached in memory after retrieval."""
        # First get should populate cache
        result1 = await chat_service.get_chat_by_id(test_chat.id, async_session)
        assert result1 is not None

        # Should now be in cache
        cached = chat_service.get_base_chat_by_id(test_chat.id)
        assert cached is not None
        assert cached.db_object.id == test_chat.id

        # Second get should use cache
        result2 = await chat_service.get_chat_by_id(test_chat.id, async_session)
        assert result2 is cached

    @pytest.mark.asyncio
    async def test_chat_with_null_task_id(self, chat_service, async_session):
        """Test creating and retrieving a chat with null task_id."""
        # Create chat with null task_id
        chat = models.Chat(task_id=None)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)

        # Should be retrievable
        result = await chat_service.get_chat_by_id(chat.id, async_session)
        assert result is not None
        assert result.db_object.task_id is None
