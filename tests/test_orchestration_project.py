import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.orchestration.project import BaseProject
from src.schemas.data import ProjectData, is_filesafe
from src.schemas.task import TaskUpdate
from src.services.registry import registry


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry services after each test to avoid cross-test contamination."""
    registry._services.clear()


class TestBaseProject:
    """Test suite for BaseProject."""

    @pytest.fixture
    def base_project(self, test_project):
        """Create a BaseProject instance for testing."""
        return BaseProject(ProjectData.model_validate(test_project))

    @pytest.fixture
    def mock_repo(self):
        """Create a mock git.Repo instance."""
        repo = MagicMock()
        repo.git = MagicMock()
        repo.git.worktree = MagicMock()
        repo.bare = True
        return repo

    def test_is_filesafe(self):
        """Test is_filesafe function."""
        assert is_filesafe("valid-name")
        assert is_filesafe("valid_name")
        assert is_filesafe("valid.name")
        assert is_filesafe("valid123")
        assert is_filesafe("VALID-NAME")

        assert not is_filesafe("invalid name")
        assert not is_filesafe("invalid/name")
        assert not is_filesafe("invalid\\name")
        assert not is_filesafe("invalid:name")
        assert not is_filesafe("invalid*name")
        assert not is_filesafe("invalid?name")
        assert not is_filesafe('invalid"name')
        assert not is_filesafe("invalid<name")
        assert not is_filesafe("invalid>name")
        assert not is_filesafe("invalid|name")

    @pytest.mark.asyncio
    async def test_create_task_success(self, base_project, mock_repo):
        """Test creating a task with valid name."""
        mock_task_service = MagicMock()
        mock_task_service.create_task = AsyncMock()
        mock_task = AsyncMock()
        mock_task_service.create_task.return_value = mock_task
        registry._services["task"] = mock_task_service

        with patch.object(base_project, "get_repo", return_value=mock_repo):
            with patch("src.orchestration.project.os.path.join") as mock_join:
                mock_join.return_value = "/tmp/project/sublimate/task1"

                result = await base_project.create_task(
                    name="task1",
                    goal="Test goal",
                    branches_from="dev",
                    settings_yaml="test: yaml",
                )

                mock_repo.git.worktree.assert_called_once_with(
                    "add", "-b", "task1", "sublimate/task1", "dev"
                )
                mock_task_service.create_task.assert_called_once()
                call_args = mock_task_service.create_task.call_args[1]["task"]
                assert call_args.name == "task1"
                assert call_args.project_id == base_project._data.id
                assert call_args.goal == "Test goal"
                assert call_args.settings_yaml == "test: yaml"
                assert result is mock_task

    @pytest.mark.asyncio
    async def test_create_task_invalid_name(self, base_project):
        with pytest.raises(ValueError, match="is not filesafe"):
            await base_project.create_task(
                name="invalid name", goal="Test goal", branches_from="dev"
            )

    @pytest.mark.asyncio
    async def test_load_task_open(self, base_project):
        mock_task_service = MagicMock()
        mock_task = AsyncMock()
        mock_task._data.open = True
        mock_task_service.get_task_by_id = AsyncMock(return_value=mock_task)
        registry._services["task"] = mock_task_service

        with patch.object(base_project, "get_worktree", return_value="/tmp/worktree"):
            result = await base_project.load_task(task_id=1, task_name="existing-task")

            assert result is mock_task
            base_project.get_worktree.assert_called_once_with("existing-task")

    @pytest.mark.asyncio
    async def test_load_task_closed(self, base_project):
        mock_task_service = MagicMock()
        mock_task = AsyncMock()
        mock_task._data.open = False
        mock_task_service.get_task_by_id = AsyncMock(return_value=mock_task)
        registry._services["task"] = mock_task_service

        with pytest.raises(ValueError, match="is closed"):
            await base_project.load_task(task_id=1, task_name="closed-task")

    @pytest.mark.asyncio
    async def test_close_task(self, base_project, mock_repo):
        mock_task_service = MagicMock()
        mock_task_service.update_task = AsyncMock()
        mock_task_service.update_task.return_value = AsyncMock()
        registry._services["task"] = mock_task_service

        with patch.object(base_project, "get_repo", return_value=mock_repo):
            with patch("src.orchestration.project.os.path.exists", return_value=True):
                with patch("src.orchestration.project.os.path.join") as mock_join:
                    mock_join.return_value = "/fake/path"

                    await base_project.close_task(
                        task_id=1, task_name="task-to-close", auto_merge=False
                    )

                    mock_task_service.update_task.assert_called_once_with(
                        1, TaskUpdate(open=False)
                    )
                    mock_repo.git.worktree.assert_called_once_with(
                        "remove", "/fake/path"
                    )
                    mock_join.assert_called_once_with(
                        base_project._data.root_dir,
                        "sublimate",
                        "task-to-close",
                    )

    @pytest.mark.asyncio
    async def test_close_task_with_auto_merge(self, base_project, mock_repo):
        mock_task_service = MagicMock()
        mock_task_service.update_task = AsyncMock()
        mock_task_service.update_task.return_value = AsyncMock()
        registry._services["task"] = mock_task_service

        with patch.object(base_project, "get_repo", return_value=mock_repo):
            with patch("src.orchestration.project.os.path.exists", return_value=True):
                with patch("src.orchestration.project.os.path.join") as mock_join:
                    mock_join.return_value = "/fake/path"
                    with patch.object(
                        base_project, "merge_task_into_dev"
                    ) as mock_merge:
                        await base_project.close_task(
                            task_id=1, task_name="task-to-close", auto_merge=True
                        )

                        mock_task_service.update_task.assert_called_once_with(
                            1, TaskUpdate(open=False)
                        )
                        mock_merge.assert_called_once_with("task-to-close")
                        mock_join.assert_called_once_with(
                            base_project._data.root_dir,
                            "sublimate",
                            "task-to-close",
                        )

    @pytest.mark.asyncio
    async def test_reopen_task(self, base_project):
        mock_task_service = MagicMock()
        mock_task_service.update_task = AsyncMock()
        mock_return = AsyncMock()
        mock_task_service.update_task.return_value = mock_return
        registry._services["task"] = mock_task_service

        with patch.object(base_project, "get_worktree", return_value="/tmp/worktree"):
            result = await base_project.reopen_task(
                task_id=1, task_name="task-to-reopen"
            )

            mock_task_service.update_task.assert_called_once_with(
                1, TaskUpdate(open=True)
            )
            base_project.get_worktree.assert_called_once_with("task-to-reopen")
            assert result is mock_return
