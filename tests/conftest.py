import pytest
import sys
import tempfile
from pathlib import Path
import os

from unittest.mock import patch, MagicMock


@pytest.fixture
def tmpdir():
    """Create a temporary directory that works on Windows."""
    if sys.platform == "win32":
        import time

        # TODO: make this better
        base_path = Path(os.getcwd()) / "tmp"
        base_path.mkdir(exist_ok=True)
        temp_path = (
            base_path
            / f"pytest_test_{os.getpid()}_{str(time.time()).replace('.', '_')}"
        )
        temp_path.mkdir(exist_ok=True)
        yield temp_path
        # Clean up - retry a few times on Windows due to file locking
        for _ in range(5):
            try:
                import shutil

                shutil.rmtree(temp_path, ignore_errors=True)
                break
            except (PermissionError, OSError):
                import time

                time.sleep(0.1)
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir


@pytest.fixture(autouse=True)
def mock_invokes():
    with (
        patch("src.orchestration.composer.BaseAgent.invoke") as mock_invoke,
        patch("src.orchestration.composer.BaseAgent.ainvoke") as mock_ainvoke,
    ):
        mock_invoke.return_value = "Mocked agent.invoke()"
        mock_ainvoke.return_value = "Mocked agent.ainvoke()"
        yield


@pytest.fixture(autouse=True)
def mock_init_chat_model():
    """Mock init_chat_model to avoid real API calls."""
    mock_model = MagicMock()
    mock_model.name = "mock-ollama-model"
    with patch(
        "langchain.chat_models.init_chat_model", return_value=mock_model
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_create_agent():
    """Mock create_agent to return a mock agent."""
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = "Mocked agent.invoke()"
    mock_agent.ainvoke.return_value = "Mocked agent.ainvoke()"
    with patch("langchain.agents.create_agent", return_value=mock_agent) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_fetch_api_key():
    """Mock fetch_api_key_for_provider to return dummy key."""
    with patch(
        "src.orchestration.composer.BaseComposer.fetch_api_key_for_provider",
        return_value="dummy-api-key",
    ) as mock:
        yield mock
