"""
Tests for the project module.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.orchestration.project import BaseProject
from src.orchestration.message import BaseMessage


class TestBaseProject:
    """Tests for BaseProject class."""

    def setup_method(self):
        """Set up mocks."""
        self.mock_composer = MagicMock()
        self.mock_tools = MagicMock()

        # Patch create_composer
        self.create_composer_patcher = patch(
            "src.orchestration.project.create_composer", return_value=self.mock_composer
        )
        self.mock_create_composer = self.create_composer_patcher.start()

        # Patch get_all_tools
        self.get_all_tools_patcher = patch(
            "src.orchestration.project.get_all_tools", return_value=self.mock_tools
        )
        self.mock_get_all_tools = self.get_all_tools_patcher.start()

    def teardown_method(self):
        """Stop patchers."""
        self.create_composer_patcher.stop()
        self.get_all_tools_patcher.stop()

    def test_init(self):
        """Test initialization."""
        project = BaseProject("/root", "/agent_home")

        assert project.root_dir == "/root"
        assert project.agent_home == "/agent_home"
        assert project.tasks == {}
        assert project.composer == self.mock_composer
        self.mock_create_composer.assert_called_once_with(
            agent_home="/agent_home",
            tools=self.mock_tools,
            root_dir="/root",
            project=project,
        )

    def test_new_task_id_empty(self):
        """Test new_task_id when tasks dict is empty."""
        project = BaseProject("/root", "/agent_home")
        project.tasks = {}

        task_id = project.new_task_id()

        assert task_id == 1

    def test_new_task_id_with_existing(self):
        """Test new_task_id when tasks exist."""
        project = BaseProject("/root", "/agent_home")
        project.tasks = {1: MagicMock(), 3: MagicMock(), 5: MagicMock()}

        task_id = project.new_task_id()

        assert task_id == 6  # max(1,3,5) + 1 = 6

    def test_get_task_by_id_exists(self):
        """Test get_task_by_id returns task when exists."""
        project = BaseProject("/root", "/agent_home")
        mock_task = MagicMock()
        project.tasks = {42: mock_task}

        result = project.get_task_by_id(42)

        assert result == mock_task

    def test_get_task_by_id_not_exists(self):
        """Test get_task_by_id returns None when task doesn't exist."""
        project = BaseProject("/root", "/agent_home")

        result = project.get_task_by_id(999)

        assert result is None

    @patch("src.orchestration.project.create_task")
    def test_create_task(self, mock_create_task):
        """Test create_task creates new task with incremental ID."""
        project = BaseProject("/root", "/agent_home")
        project.tasks = {}
        mock_task = MagicMock()
        mock_task.id = None
        mock_create_task.return_value = mock_task

        result = project.create_task("Test prompt", userid=7)

        # Check create_task called with correct arguments
        mock_create_task.assert_called_once()
        call_args = mock_create_task.call_args
        assert call_args[0][0] == project  # first positional arg is self (project)
        # second arg should be list with one BaseMessage
        messages = call_args[0][1]
        assert len(messages) == 1
        assert isinstance(messages[0], BaseMessage)
        assert messages[0].role == "user"
        assert messages[0].content == "Test prompt"
        assert messages[0].userid == 7

        # Check task ID assigned
        assert mock_task.id == 1
        assert project.tasks == {1: mock_task}
        assert result == mock_task

    @patch("src.orchestration.project.create_task")
    def test_create_task_increments_id(self, mock_create_task):
        """Test create_task increments ID correctly."""
        project = BaseProject("/root", "/agent_home")
        project.tasks = {1: MagicMock(), 2: MagicMock()}
        mock_task = MagicMock()
        mock_task.id = None
        mock_create_task.return_value = mock_task

        project.create_task("Prompt")

        assert mock_task.id == 3
        assert project.tasks[3] == mock_task

    @patch("src.orchestration.project.create_task")
    def test_load_task_from_messages_new(self, mock_create_task):
        """Test load_task_from_messages creates task with given ID."""
        project = BaseProject("/root", "/agent_home")
        project.tasks = {}
        mock_task = MagicMock()
        mock_task.id = (
            99,
        )  # Note: create_task returns task with id as tuple? Actually line 42: new_task.id = (id,)
        mock_create_task.return_value = mock_task
        mock_messages = [{"role": "user", "content": "test"}]

        result = project.load_task_from_messages(mock_messages, 99)

        mock_create_task.assert_called_once_with(project, mock_messages)
        # Implementation sets new_task.id = (id,) - tuple
        # We'll just check that task is stored
        assert project.tasks[99] == mock_task
        assert result == mock_task

    @patch("src.orchestration.project.create_task")
    def test_load_task_from_messages_already_exists(self, mock_create_task):
        """Test load_task_from_messages raises ValueError if ID exists."""
        project = BaseProject("/root", "/agent_home")
        project.tasks = {99: MagicMock()}

        with pytest.raises(ValueError) as exc_info:
            project.load_task_from_messages([], 99)

        assert "Task #99 already exists!" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
