import pytest
from unittest.mock import patch, AsyncMock
from src.services.task import TaskService
from src.schemas.task import TaskCreate, TaskUpdate
from src.db import models


class TestTaskService:
    """Test suite for TaskService."""

    @pytest.fixture
    def task_service(self):
        """Create a fresh TaskService instance for each test."""
        return TaskService()

    @pytest.mark.asyncio
    async def test_create_task(self, task_service, async_session, test_project):
        """Test creating a new task."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            with patch("src.services.chat.get_db_session", return_value=async_session):
                # Mock project_service.get_project_by_id to return test project
                mock_project = AsyncMock()
                mock_project.db_object = test_project
                with patch(
                    "src.services.project.project_service.get_project_by_id",
                    return_value=mock_project,
                ):
                    task_create = TaskCreate(
                        name="new-task",
                        project_id=test_project.id,
                        root_dir="/tmp/new_task",
                        settings_yaml="task: settings",
                        todos="Task todos",
                        goal="Example goal",
                    )

                    result = await task_service.create_task(task_create)

                    assert result is not None
                    assert result.db_object.name == "new-task"
                    assert result.db_object.project_id == test_project.id
                    assert result.db_object.todos == "Task todos"

    @pytest.mark.asyncio
    async def test_create_task_invalid_name(
        self, task_service, async_session, test_project
    ):
        """Test creating a task with invalid (non-filesafe) name."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            with patch("src.services.chat.get_db_session", return_value=async_session):
                mock_project = AsyncMock()
                mock_project.db_object = test_project
                with patch(
                    "src.services.project.project_service.get_project_by_id",
                    return_value=mock_project,
                ):
                    task_create = TaskCreate(
                        name="invalid name with spaces",
                        project_id=test_project.id,
                        root_dir="/tmp/invalid_task",
                        settings_yaml="task: settings",
                        goal="Example goal",
                    )

                    # Should raise ValueError for non-filesafe name
                    with pytest.raises(ValueError, match="is not filesafe"):
                        await task_service.create_task(task_create)

    @pytest.mark.asyncio
    async def test_create_task_project_not_found(self, task_service, async_session):
        """Test creating a task for non-existent project returns None."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            with patch("src.services.chat.get_db_session", return_value=async_session):
                with patch(
                    "src.services.project.project_service.get_project_by_id",
                    return_value=None,
                ):
                    task_create = TaskCreate(
                        name="test-task",
                        project_id=9999,
                        root_dir="/tmp/test_task",
                        settings_yaml="task: settings",
                        goal="Example goal",
                    )

                    result = await task_service.create_task(task_create)
                    assert result is None

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, task_service, async_session, test_project):
        """Test retrieving a task by ID."""
        # First create a task
        task = models.Task(
            name="test-task",
            project_id=test_project.id,
            root_dir="/tmp/test_task",
            settings_yaml="task: settings",
            todos="Test todos",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        # Create a chat for the task
        chat = models.Chat(task_id=task.id)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)
        # Link task to chat
        task.chat_id = chat.id
        await async_session.commit()
        await async_session.refresh(task)

        with patch("src.services.task.get_db_session", return_value=async_session):
            result = await task_service.get_task_by_id(task.id)

            assert result is not None
            assert result.db_object.id == task.id
            assert result.db_object.name == "test-task"

    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, task_service, async_session):
        """Test retrieving a non-existent task returns None."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            result = await task_service.get_task_by_id(9999)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_tasks_by_project(
        self, task_service, async_session, test_project
    ):
        """Test retrieving all tasks for a project."""
        # Create multiple tasks for the project
        task1 = models.Task(
            name="task-1",
            project_id=test_project.id,
            root_dir="/tmp/task1",
            settings_yaml="task1: settings",
        )
        task2 = models.Task(
            name="task-2",
            project_id=test_project.id,
            root_dir="/tmp/task2",
            settings_yaml="task2: settings",
        )
        async_session.add_all([task1, task2])
        await async_session.commit()
        await async_session.refresh(task1)
        await async_session.refresh(task2)
        # Create chats for each task
        chat1 = models.Chat(task_id=task1.id)
        chat2 = models.Chat(task_id=task2.id)
        async_session.add_all([chat1, chat2])
        await async_session.commit()
        await async_session.refresh(chat1)
        await async_session.refresh(chat2)
        # Link tasks to chats
        task1.chat_id = chat1.id
        task2.chat_id = chat2.id
        await async_session.commit()
        await async_session.refresh(task1)
        await async_session.refresh(task2)

        with patch("src.services.task.get_db_session", return_value=async_session):
            result = await task_service.get_tasks_by_project(test_project.id)

            assert len(result) >= 2
            task_names = [t.db_object.name for t in result]
            assert "task-1" in task_names
            assert "task-2" in task_names

    @pytest.mark.asyncio
    async def test_get_all_tasks(self, task_service, async_session, test_task):
        """Test retrieving all tasks."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            result = await task_service.get_all_tasks()

            # Should have at least the tasks we created in fixtures
            assert len(result) >= 1
            # Verify our test task is in the results
            task_ids = [t.db_object.id for t in result]
            assert test_task.id in task_ids

    @pytest.mark.asyncio
    async def test_update_task(self, task_service, async_session, test_project):
        """Test updating a task."""
        # Create a task to update
        task = models.Task(
            name="original-task",
            project_id=test_project.id,
            root_dir="/tmp/original_task",
            settings_yaml="original: settings",
            todos="Original todos",
            open=True,
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        # Create a chat for the task
        chat = models.Chat(task_id=task.id)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)
        # Link task to chat
        task.chat_id = chat.id
        await async_session.commit()
        await async_session.refresh(task)

        with patch("src.services.task.get_db_session", return_value=async_session):
            task_update = TaskUpdate(
                name="updated-task",
                project_id=test_project.id,
                root_dir="/tmp/updated_task",
                settings_yaml="updated: settings",
                todos="Updated todos",
                open=False,
            )

            result = await task_service.update_task(task.id, task_update)

            assert result is not None
            assert result.db_object.name == "updated-task"
            assert result.db_object.root_dir == "/tmp/updated_task"
            assert result.db_object.todos == "Updated todos"
            assert not result.db_object.open

    @pytest.mark.asyncio
    async def test_update_task_partial(self, task_service, async_session, test_project):
        """Test partially updating a task."""
        task = models.Task(
            name="partial-task",
            project_id=test_project.id,
            root_dir="/tmp/partial_task",
            settings_yaml="partial: settings",
            todos="Partial todos",
            open=True,
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        # Create a chat for the task
        chat = models.Chat(task_id=task.id)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)
        # Link task to chat
        task.chat_id = chat.id
        await async_session.commit()
        await async_session.refresh(task)

        with patch("src.services.task.get_db_session", return_value=async_session):
            # Only update the todos field
            task_update = TaskUpdate(todos="New todos only")

            result = await task_service.update_task(task.id, task_update)

            assert result is not None
            assert result.db_object.todos == "New todos only"
            # Other fields should remain unchanged
            assert result.db_object.name == "partial-task"
            assert result.db_object.open

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, task_service, async_session):
        """Test updating a non-existent task returns None."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            task_update = TaskUpdate(name="nonexistent-task")

            result = await task_service.update_task(9999, task_update)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_task(self, task_service, async_session, test_project):
        """Test deleting a task."""
        # Create a task to delete
        task = models.Task(
            name="delete-task",
            project_id=test_project.id,
            root_dir="/tmp/delete_task",
            settings_yaml="delete: settings",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        # Create a chat for the task
        chat = models.Chat(task_id=task.id)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)
        # Link task to chat
        task.chat_id = chat.id
        await async_session.commit()
        await async_session.refresh(task)

        with patch("src.services.task.get_db_session", return_value=async_session):
            # First verify task exists
            result = await task_service.get_task_by_id(task.id)
            assert result is not None

            # Delete the task
            delete_result = await task_service.delete_task(task.id)
            assert delete_result is True

            # Verify task no longer exists
            result = await task_service.get_task_by_id(task.id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, task_service, async_session):
        """Test deleting a non-existent task returns False."""
        with patch("src.services.task.get_db_session", return_value=async_session):
            result = await task_service.delete_task(9999)
            assert result is False

    @pytest.mark.asyncio
    async def test_filesafe_validation(self, task_service):
        """Test filesafe name validation."""
        # Valid names
        assert task_service._is_filesafe("valid-name")
        assert task_service._is_filesafe("valid_name")
        assert task_service._is_filesafe("valid.name")
        assert task_service._is_filesafe("valid123")
        assert task_service._is_filesafe("VALID-NAME")

        # Invalid names
        assert not task_service._is_filesafe("invalid name")  # space
        assert not task_service._is_filesafe("invalid/name")  # slash
        assert not task_service._is_filesafe("invalid\\name")  # backslash
        assert not task_service._is_filesafe("invalid:name")  # colon
        assert not task_service._is_filesafe("invalid*name")  # asterisk
        assert not task_service._is_filesafe("invalid?name")  # question mark
        assert not task_service._is_filesafe('invalid"name')  # quote
        assert not task_service._is_filesafe("invalid<name")  # less than
        assert not task_service._is_filesafe("invalid>name")  # greater than
        assert not task_service._is_filesafe("invalid|name")  # pipe

    @pytest.mark.asyncio
    async def test_get_base_task_by_id(self, task_service, async_session, test_project):
        """Test getting task from memory cache."""
        # Create a task
        task = models.Task(
            name="cache-task",
            project_id=test_project.id,
            root_dir="/tmp/cache_task",
            settings_yaml="cache: settings",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        # Create a chat for the task
        chat = models.Chat(task_id=task.id)
        async_session.add(chat)
        await async_session.commit()
        await async_session.refresh(chat)
        # Link task to chat
        task.chat_id = chat.id
        await async_session.commit()
        await async_session.refresh(task)

        # First get the task to populate cache
        with patch("src.services.task.get_db_session", return_value=async_session):
            result = await task_service.get_task_by_id(task.id)
            assert result is not None

        # Now get from cache
        cached_result = task_service.get_base_task_by_id(task.id)
        assert cached_result is not None
        assert cached_result.db_object.id == task.id

    @pytest.mark.asyncio
    async def test_get_base_task_by_id_not_found(self, task_service):
        """Test getting non-existent task from memory returns None."""
        result = task_service.get_base_task_by_id(9999)
        assert result is None
