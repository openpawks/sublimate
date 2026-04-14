"""
Tests for file access permissions.
"""

import pytest
from pathlib import Path

from src.orchestration.composer import BaseAgent
from langchain.chat_models import init_chat_model


class TestFileAccessPermissions:
    """Test file access control patterns."""

    def test_pattern_matching_simple(self, tmpdir):
        """Test simple glob patterns."""
        agent_home = Path(tmpdir) / "agents"
        agent_home.mkdir()
        root = Path(tmpdir)
        # Create agent with empty tools
        agent = BaseAgent(
            name="test",
            agent_home=agent_home,
            model=init_chat_model("ollama:qwen3.5:0.8b"),
            tools=[],
            root_folder=str(root),
            file_access=["./*.py"],
            read_only_file_access=["./docs/*"],
            deny_file_access=["./secrets/*"],
        )
        # Test matching
        assert agent._match_pattern("main.py", "*.py") is True
        assert agent._match_pattern("main.py", "./*.py") is True
        assert agent._match_pattern("src/main.py", "*.py") is False  # no directory
        assert agent._match_pattern("src/main.py", "**/*.py") is True
        # Test deny patterns
        assert agent._match_pattern("secrets/key.txt", "secrets/*") is True
        # Test read-only patterns
        assert agent._match_pattern("docs/readme.md", "docs/*") is True

    def test_check_file_access_deny(self, tmpdir):
        """Test deny file access overrides."""
        agent_home = Path(tmpdir) / "agents"
        agent_home.mkdir()
        root = Path(tmpdir)
        agent = BaseAgent(
            name="test",
            agent_home=agent_home,
            model=init_chat_model("ollama:qwen3.5:0.8b"),
            tools=[],
            root_folder=str(root),
            file_access=["./*"],
            deny_file_access=["./private/*"],
        )
        # Create a file path relative to root
        file_ok = root / "public.txt"
        file_deny = root / "private" / "secret.txt"
        file_deny.parent.mkdir()
        # Check access
        assert agent.check_file_access(str(file_ok), mode="read") is True
        assert agent.check_file_access(str(file_ok), mode="write") is True
        assert agent.check_file_access(str(file_deny), mode="read") is False
        assert agent.check_file_access(str(file_deny), mode="write") is False

    def test_check_file_access_read_only(self, tmpdir):
        """Test read-only file access."""
        agent_home = Path(tmpdir) / "agents"
        agent_home.mkdir()
        root = Path(tmpdir)
        agent = BaseAgent(
            name="test",
            agent_home=agent_home,
            model=init_chat_model("ollama:qwen3.5:0.8b"),
            tools=[],
            root_folder=str(root),
            file_access=["./*"],
            read_only_file_access=["./logs/*"],
        )
        log_file = root / "logs" / "app.log"
        log_file.parent.mkdir()
        assert agent.check_file_access(str(log_file), mode="read") is True
        assert agent.check_file_access(str(log_file), mode="write") is False
        # Other files are read/write
        other = root / "other.txt"
        assert agent.check_file_access(str(other), mode="write") is True

    def test_check_file_access_no_match(self, tmpdir):
        """If no pattern matches, deny access."""
        agent_home = Path(tmpdir) / "agents"
        agent_home.mkdir()
        root = Path(tmpdir)
        agent = BaseAgent(
            name="test",
            agent_home=agent_home,
            model=init_chat_model("ollama:qwen3.5:0.8b"),
            tools=[],
            root_folder=str(root),
            file_access=["./src/*"],  # only src directory
        )
        # File outside src
        outside = root / "other.txt"
        assert agent.check_file_access(str(outside), mode="read") is False
        # File inside src
        inside = root / "src" / "main.py"
        inside.parent.mkdir()
        assert agent.check_file_access(str(inside), mode="read") is True

    def test_absolute_paths(self, tmpdir):
        """Test with absolute paths."""
        agent_home = Path(tmpdir) / "agents"
        agent_home.mkdir()
        root = Path(tmpdir)
        agent = BaseAgent(
            name="test",
            agent_home=agent_home,
            model=init_chat_model("ollama:qwen3.5:0.8b"),
            tools=[],
            root_folder=str(root),
            file_access=["./*"],
        )
        abs_path = root / "test.txt"
        assert agent.check_file_access(str(abs_path), mode="read") is True
        # Path outside root
        outside = Path("/tmp/outside.txt")
        assert agent.check_file_access(str(outside), mode="read") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
