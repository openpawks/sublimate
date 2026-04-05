import pytest

from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_invokes():
    with (
        patch("src.composer.composer.BaseAgent.invoke") as mock_invoke,
        patch("src.composer.composer.BaseAgent.ainvoke") as mock_ainvoke,
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
        "src.composer.composer.BaseComposer.fetch_api_key_for_provider",
        return_value="dummy-api-key",
    ) as mock:
        yield mock
