import pytest

from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_invokes():
    with patch("src.composer.composer.BaseAgent.invoke") as mock_invoke:
        mock_invoke.return_value = "Mocked agent.invoke()"
        yield
