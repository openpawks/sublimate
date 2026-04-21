import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.orchestration.project import BaseProject
from src.db import models
from src.schemas.task import TaskUpdate


class TestBaseProject:
    """Test suite for BaseProject."""

    @pytest.fixture
    def base_project(self, test_project):
        """Create a BaseProject instance for testing."""
        return BaseProject(test_project)

    @pytest.fixture
    def mock_repo(self):
        """Create a mock git.Repo instance."""
        repo = MagicMock()
        repo.git = MagicMock()
        repo.git.worktree = MagicMock()
        repo.bare = True
        return repo

    def test_is_filesafe(self):
        """Test _is_filesafe static method."""
        assert BaseProject._is_filesafe("valid-name")
        assert BaseProject._is_filesafe("valid_name")
        assert BaseProject._is_filesafe("valid.name")
        assert BaseProject._is_filesafe("valid123")
        assert BaseProject._is_filesafe("VALID-NAME")

        assert not BaseProject._is_filesafe("invalid name")  # space
        assert not BaseProject._is_filesafe("invalid/name")  # slash
        assert not BaseProject._is_filesafe("invalid\\name")  # backslash
        assert not BaseProject._is_filesafe("invalid:name")  # colon
        assert not BaseProject._is_filesafe("invalid*name")  # asterisk
        assert not BaseProject._is_filesafe("invalid?name")  # question mark
        assert not BaseProject._is_filesafe('invalid"name')  # quote
        assert not BaseProject._is_filesafe("invalid<name")  # less than
        assert not BaseProject._is_filesafe("invalid>name")  # greater than
        assert not BaseProject._is_filesafe("invalid|name")  # pipe

    @pytest.mark.asyncio
    async def test_create_task_success(self, base_project, mock_repo):
        """Test creating a task with valid name."""
        with patch.object(base_project, "get_repo", return_value=mock_repo):
            with patch("src.orchestration.project.os.path.join") as mock_join:
                mock_join.return_value = "/tmp/project/sublimate/task1"
                with patch(
                    "src.orchestration.project.task_service.create_task"
                ) as mock_create:
                    mock_task = AsyncMock()
                    mock_create.return_value = mock_task

                    result = await base_project.create_task(
                        name="task1",
                        goal="Test goal",
                        branches_from="dev",
                        settings_yaml="test: yaml",
                    )

                    # Verify git worktree add called
                    mock_repo.git.worktree.assert_called_once_with(
                        "add", "-b", "task1", "sublimate/task1", "dev"
                    )
                    # Verify task_service.create_task called with correct args
                    mock_create.assert_called_once()
                    call_args = mock_create.call_args[1]["task"]
                    assert call_args.name == "task1"
                    assert call_args.project_id == base_project.db_object.id
                    assert call_args.goal == "Test goal"
                    assert call_args.settings_yaml == "test: yaml"
                    assert result is mock_task

    @pytest.mark.asyncio
    async def test_create_task_invalid_name(self, base_project):
        """Test creating a task with invalid name raises ValueError."""
        with pytest.raises(ValueError, match="is not filesafe"):
            await base_project.create_task(
                name="invalid name", goal="Test goal", branches_from="dev"
            )

    @pytest.mark.asyncio
    async def test_load_task_open(self, base_project):
        """Test loading an open task."""
        task_db_obj = MagicMock(spec=models.Task)
        task_db_obj.open = True
        task_db_obj.name = "existing-task"

        with patch.object(base_project, "get_worktree", return_value="/tmp/worktree"):
            result = await base_project.load_task(task_db_obj)

            assert result is task_db_obj
            base_project.get_worktree.assert_called_once_with("existing-task")

    @pytest.mark.asyncio
    async def test_load_task_closed(self, base_project):
        """Test loading a closed task raises ValueError."""
        task_db_obj = MagicMock(spec=models.Task)
        task_db_obj.open = False
        task_db_obj.name = "closed-task"

        with pytest.raises(ValueError, match="is closed"):
            await base_project.load_task(task_db_obj)

    @pytest.mark.asyncio
    async def test_close_task(self, base_project, mock_repo):
        """Test closing a task."""
        task_db_obj = MagicMock(spec=models.Task)
        task_db_obj.id = 1
        task_db_obj.name = "task-to-close"

        with patch.object(base_project, "get_repo", return_value=mock_repo):
            with patch("src.orchestration.project.os.path.exists", return_value=True):
                with patch("src.orchestration.project.os.path.join") as mock_join:
                    mock_join.return_value = "/fake/path"
                    with patch(
                        "src.orchestration.project.task_service.update_task"
                    ) as mock_update:
                        mock_update.return_value = AsyncMock()

                        await base_project.close_task(task_db_obj, auto_merge=False)

                        # Verify task update called with TaskUpdate(open=False)
                        mock_update.assert_called_once_with(1, TaskUpdate(open=False))
                        # Verify worktree remove called with correct path
                        mock_repo.git.worktree.assert_called_once_with(
                            "remove", "/fake/path"
                        )
                        # Verify os.path.join called with correct arguments
                        mock_join.assert_called_once_with(
                            base_project.db_object.root_dir,
                            "sublimate",
                            task_db_obj.name,
                        )

    @pytest.mark.asyncio
    async def test_close_task_with_auto_merge(self, base_project, mock_repo):
        """Test closing a task with auto_merge=True."""
        task_db_obj = MagicMock(spec=models.Task)
        task_db_obj.id = 1
        task_db_obj.name = "task-to-close"

        with patch.object(base_project, "get_repo", return_value=mock_repo):
            with patch("src.orchestration.project.os.path.exists", return_value=True):
                with patch("src.orchestration.project.os.path.join") as mock_join:
                    mock_join.return_value = "/fake/path"
                    with patch(
                        "src.orchestration.project.task_service.update_task"
                    ) as mock_update:
                        with patch.object(
                            base_project, "merge_task_into_dev"
                        ) as mock_merge:
                            mock_update.return_value = AsyncMock()

                            await base_project.close_task(task_db_obj, auto_merge=True)

                            mock_update.assert_called_once_with(
                                1, TaskUpdate(open=False)
                            )
                            mock_merge.assert_called_once_with(task_db_obj)
                            mock_join.assert_called_once_with(
                                base_project.db_object.root_dir,
                                "sublimate",
                                task_db_obj.name,
                            )

    @pytest.mark.asyncio
    async def test_reopen_task(self, base_project):
        """Test reopening a closed task."""
        task_db_obj = MagicMock(spec=models.Task)
        task_db_obj.id = 1
        task_db_obj.name = "task-to-reopen"

        with patch("src.orchestration.project.task_service.update_task") as mock_update:
            mock_update.return_value = AsyncMock()
            with patch.object(
                base_project, "get_worktree", return_value="/tmp/worktree"
            ):
                result = await base_project.reopen_task(task_db_obj)

                mock_update.assert_called_once_with(1, TaskUpdate(open=True))
                base_project.get_worktree.assert_called_once_with("task-to-reopen")
                assert result is mock_update.return_value
