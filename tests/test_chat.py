"""
Tests for the chat module.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.orchestration.chat import BaseChat
from src.orchestration.message import BaseMessage


class TestBaseChat:
    """Tests for BaseChat class."""

    def test_init_empty(self):
        """Test initialization creates empty messages list."""
        chat = BaseChat()

        assert chat.messages == []
        assert isinstance(chat.messages, list)

    def test_from_messages(self):
        """Test static method from_messages."""
        mock_messages = [
            BaseMessage("user", "Hello"),
            BaseMessage("assistant", "Hi there"),
        ]

        chat = BaseChat.from_messages(mock_messages)

        assert chat.messages == mock_messages
        assert len(chat.messages) == 2
        assert chat.messages[0].role == "user"
        assert chat.messages[1].content == "Hi there"

    def test_from_messages_with_args_kwargs(self):
        """Test from_messages passes args/kwargs to constructor."""
        # BaseChat has no extra args, but test passes through
        chat = BaseChat.from_messages([], some_arg="value")
        assert chat.messages == []
        # No error raised

    def test_get_messages_empty(self):
        """Test get_messages with empty chat."""
        chat = BaseChat()

        messages = chat.get_messages()

        assert messages == []
        assert isinstance(messages, list)

    def test_get_messages_with_content(self):
        """Test get_messages returns proper dict format."""
        chat = BaseChat()
        msg1 = BaseMessage("user", "Hello", userid=1, username="alice")
        msg2 = BaseMessage("assistant", "Hi", userid=2, username="bot")
        chat.messages = [msg1, msg2]

        messages = chat.get_messages()

        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "Hi"}
        # Note: userid and username are not included in get_messages output

    def test_was_created_at_empty(self):
        """Test was_created_at on empty chat raises IndexError."""
        chat = BaseChat()

        with pytest.raises(IndexError):
            chat.was_created_at()

    def test_was_created_at_with_messages(self):
        """Test was_created_at returns timestamp of first message."""
        chat = BaseChat()
        mock_time = 1234567890.0
        msg = BaseMessage("user", "test")
        with patch.object(msg, "created_at", mock_time):
            chat.messages = [msg]

            result = chat.was_created_at()
            assert result == mock_time

    def test_was_last_updated_at_empty(self):
        """Test was_last_updated_at on empty chat raises IndexError."""
        chat = BaseChat()

        with pytest.raises(IndexError):
            chat.was_last_updated_at()

    def test_was_last_updated_at_with_messages(self):
        """Test was_last_updated_at returns timestamp of last message."""
        chat = BaseChat()
        mock_time1 = 1000.0
        mock_time2 = 2000.0
        msg1 = BaseMessage("user", "first")
        msg2 = BaseMessage("assistant", "second")
        with patch.object(msg1, "created_at", mock_time1):
            with patch.object(msg2, "created_at", mock_time2):
                chat.messages = [msg1, msg2]

                result = chat.was_last_updated_at()
                assert result == mock_time2

    def test_add_message(self):
        """Test add_message creates new BaseMessage and appends."""
        chat = BaseChat()

        with patch("src.orchestration.chat.BaseMessage") as MockMessage:
            mock_msg = MagicMock()
            MockMessage.return_value = mock_msg

            chat.add_message("assistant", "Test content", userid=5, username="test")

            MockMessage.assert_called_once_with(
                "assistant", "Test content", userid=5, username="test"
            )
            assert chat.messages == [mock_msg]

    def test_add_message_multiple(self):
        """Test adding multiple messages."""
        chat = BaseChat()

        chat.add_message("user", "Hello")
        chat.add_message("assistant", "Hi")

        assert len(chat.messages) == 2
        assert chat.messages[0].role == "user"
        assert chat.messages[0].content == "Hello"
        assert chat.messages[1].role == "assistant"
        assert chat.messages[1].content == "Hi"

    def test_message_ordering(self):
        """Test that messages maintain order."""
        chat = BaseChat()

        timestamps = []
        for i in range(5):
            time.sleep(0.001)  # ensure increasing timestamps
            chat.add_message("user", f"Message {i}")
            timestamps.append(chat.messages[-1].created_at)

        # Verify timestamps increase
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i - 1]

        # Verify order matches insertion order
        for i, msg in enumerate(chat.messages):
            assert msg.content == f"Message {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
