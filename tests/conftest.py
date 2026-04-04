import pytest

@pytest.fixture(autouse=True)
def mock_invokes():
    with patch("src.composer.BaseAgent.invoke") as mock_invoke:
        mock_invoke.return_value = "Mocked agent.invoke()"
        yield
