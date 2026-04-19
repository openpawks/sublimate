import pytest
from unittest.mock import patch
from src.services.agent import AgentService
from src.schemas.agent import AgentCreate, AgentUpdate
from src.db import models


class TestAgentService:
    """Test suite for AgentService."""

    @pytest.fixture
    def agent_service(self):
        """Create a fresh AgentService instance for each test."""
        return AgentService()

    @pytest.mark.asyncio
    async def test_create_agent(
        self, agent_service, async_session, test_project, test_provider
    ):
        """Test creating a new agent."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            agent_create = AgentCreate(
                name="New Agent",
                project_id=test_project.id,
                provider_id=test_provider.id,
                model_name="test-model-v2",
                prompt="New agent prompt",
                heartbeat_prompt="New heartbeat prompt",
                settings_yaml="new: settings",
            )

            result = await agent_service.create_agent(agent_create)

            assert result is not None
            assert result.name == "New Agent"
            assert result.db_object.project_id == test_project.id
            assert result.db_object.provider_id == test_provider.id
            assert result.db_object.model_name == "test-model-v2"
            assert result.db_object.prompt == "New agent prompt"

    @pytest.mark.asyncio
    async def test_get_agent_by_id(self, agent_service, async_session, test_agent):
        """Test retrieving an agent by ID."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            result = await agent_service.get_agent_by_id(test_agent.id)

            assert result is not None
            assert result.db_object.id == test_agent.id
            assert result.db_object.name == test_agent.name
            assert result.db_object.project_id == test_agent.project_id

    @pytest.mark.asyncio
    async def test_get_agent_by_id_not_found(self, agent_service, async_session):
        """Test retrieving a non-existent agent returns None."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            result = await agent_service.get_agent_by_id(9999)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_agents_by_project(
        self, agent_service, async_session, test_project, test_provider
    ):
        """Test retrieving all agents for a project."""
        # Create multiple agents for the project
        agent1 = models.Agent(
            name="Agent One",
            project_id=test_project.id,
            provider_id=test_provider.id,
            model_name="model-one",
            prompt="Agent one prompt",
        )
        agent2 = models.Agent(
            name="Agent Two",
            project_id=test_project.id,
            provider_id=test_provider.id,
            model_name="model-two",
            prompt="Agent two prompt",
        )
        async_session.add_all([agent1, agent2])
        await async_session.commit()

        with patch("src.services.agent.get_db_session", return_value=async_session):
            result = await agent_service.get_agents_by_project(test_project.id)

            assert len(result) >= 2  # Should have at least the two agents
            agent_names = [a.db_object.name for a in result]
            assert "Agent One" in agent_names
            assert "Agent Two" in agent_names

    @pytest.mark.asyncio
    async def test_get_all_agents(self, agent_service, async_session, test_agent):
        """Test retrieving all agents."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            result = await agent_service.get_all_agents()

            assert len(result) >= 1
            assert any(a.db_object.id == test_agent.id for a in result)

    @pytest.mark.asyncio
    async def test_update_agent(self, agent_service, async_session, test_agent):
        """Test updating an agent."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            agent_update = AgentUpdate(
                name="Updated Agent",
                project_id=test_agent.project_id,
                provider_id=test_agent.provider_id,
                model_name="updated-model",
                prompt="Updated prompt",
                heartbeat_prompt="Updated heartbeat prompt",
                settings_yaml="updated: settings",
            )

            result = await agent_service.update_agent(test_agent.id, agent_update)

            assert result is not None
            assert result.db_object.name == "Updated Agent"
            assert result.db_object.model_name == "updated-model"
            assert result.db_object.prompt == "Updated prompt"
            assert result.db_object.settings_yaml == "updated: settings"

    @pytest.mark.asyncio
    async def test_update_agent_partial(self, agent_service, async_session, test_agent):
        """Test partially updating an agent."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            # Only update the name
            agent_update = AgentUpdate(name="Partially Updated Agent")

            result = await agent_service.update_agent(test_agent.id, agent_update)

            assert result is not None
            assert result.db_object.name == "Partially Updated Agent"
            # Other fields should remain unchanged
            assert result.db_object.prompt == test_agent.prompt
            assert result.db_object.model_name == test_agent.model_name

    @pytest.mark.asyncio
    async def test_update_agent_not_found(self, agent_service, async_session):
        """Test updating a non-existent agent returns None."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            agent_update = AgentUpdate(name="Nonexistent Agent")

            result = await agent_service.update_agent(9999, agent_update)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_agent(self, agent_service, async_session, test_agent):
        """Test deleting an agent."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            # First verify agent exists
            result = await agent_service.get_agent_by_id(test_agent.id)
            assert result is not None

            # Delete the agent
            delete_result = await agent_service.delete_agent(test_agent.id)
            assert delete_result is True

            # Verify agent no longer exists
            result = await agent_service.get_agent_by_id(test_agent.id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, agent_service, async_session):
        """Test deleting a non-existent agent returns False."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            result = await agent_service.delete_agent(9999)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_agent_factory_by_id(self, agent_service, test_agent):
        """Test getting agent factory from memory cache."""
        # First add agent to memory
        agent_service.agents_in_memory[test_agent.id] = "mock_agent_factory"

        result = agent_service.get_agent_factory_by_id(test_agent.id)
        assert result == "mock_agent_factory"

    @pytest.mark.asyncio
    async def test_get_agent_factory_by_id_not_found(self, agent_service):
        """Test getting non-existent agent factory from memory returns None."""
        result = agent_service.get_agent_factory_by_id(9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_agent_memory_cache(self, agent_service, async_session, test_agent):
        """Test that agents are cached in memory after retrieval."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            # First get should populate cache
            result1 = await agent_service.get_agent_by_id(test_agent.id)
            assert result1 is not None

            # Should now be in cache
            cached = agent_service.get_agent_factory_by_id(test_agent.id)
            assert cached is not None
            assert cached.db_object.id == test_agent.id

            # Second get should use cache
            result2 = await agent_service.get_agent_by_id(test_agent.id)
            assert result2 is cached

    @pytest.mark.asyncio
    async def test_create_agent_with_empty_fields(
        self, agent_service, async_session, test_project, test_provider
    ):
        """Test creating an agent with empty optional fields."""
        with patch("src.services.agent.get_db_session", return_value=async_session):
            agent_create = AgentCreate(
                name="Minimal Agent",
                project_id=test_project.id,
                provider_id=test_provider.id,
                model_name="minimal-model",
                prompt="",  # Empty prompt
                heartbeat_prompt="",  # Empty heartbeat prompt
                settings_yaml="",  # Empty settings
            )

            result = await agent_service.create_agent(agent_create)

            assert result is not None
            assert result.db_object.name == "Minimal Agent"
            assert result.db_object.prompt == ""
            assert result.db_object.heartbeat_prompt == ""
            assert result.db_object.settings_yaml == ""
