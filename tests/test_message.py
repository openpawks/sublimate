"""
Tests for the message module.
"""

import pytest
import time
from unittest.mock import patch

from src.orchestration.message import BaseMessage


class TestBaseMessage:
    """Tests for BaseMessage class."""

    def test_init_basic(self):
        """Test basic initialization."""
        msg = BaseMessage("user", "Hello, world!")

        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.userid == 0
        assert msg.username == ""
        assert isinstance(msg.created_at, float)
        assert msg.created_at > 0

    def test_init_with_userid_and_username(self):
        """Test initialization with userid and username."""
        msg = BaseMessage("assistant", "I'm an AI", userid=42, username="ai_bot")

        assert msg.role == "assistant"
        assert msg.content == "I'm an AI"
        assert msg.userid == 42
        assert msg.username == "ai_bot"
        assert isinstance(msg.created_at, float)

    def test_created_at_timestamp(self):
        """Test that created_at is a reasonable timestamp."""
        before = time.time()
        msg = BaseMessage("user", "test")
        after = time.time()

        assert before <= msg.created_at <= after

    def test_role_assignment(self):
        """Test different role assignments."""
        roles = ["user", "assistant", "system", "developer", "coder"]
        for role in roles:
            msg = BaseMessage(role, "content")
            assert msg.role == role

    @patch("time.time")
    def test_created_at_uses_time(self, mock_time):
        """Test that created_at uses time.time()."""
        mock_time.return_value = 1234567890.123
        msg = BaseMessage("user", "test")

        assert msg.created_at == 1234567890.123


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
