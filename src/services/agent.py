from src.orchestration.agent import AgentFactory
from src.backend import models
from src.backend.database import get_db

from src.schemas.agent import AgentCreate

from sqlalchemy import select


class AgentService:
    def __init__(self):
        self.agents_in_memory = {}

    def get_agent_factory_by_id(self, id: int):
        """
        Get AgentFactory by id, from memory

        Args:
            id: agent id
        """
        return self.agents_in_memory.get(id)

    def get_agent_factory(self, db_object: models.Agent):
        """
        Load AgentFactory into memory
        """
        agent = self.agents_in_memory.get(db_object.id)
        if agent:
            return agent

        self.agents_in_memory[db_object.id] = AgentFactory(
            db_object=db_object,
        )

        return self.agents_in_memory.get(db_object.id)

    def get_agent_by_id(self, id: int) -> AgentFactory:
        """
        Get agent object by id (AgentFactory object)

        Args:
            id: agent id
        """
        db = await get_db()

        agent_db = await db.execute(select(models.Agent.id == id)).scalars().first()

        if agent_db:
            return self.get_agent_factory(agent_db)
        else:
            return None

    async def create_agent_db(
        self,
        agent: AgentCreate,
    ):
        """
        Create a new agent in the database
        """
        db = await get_db()

        new_agent = models.Agent(
            name=agent.name,
            project_id=agent.project_id,
            provider_id=agent.provider_id,
            prompt=agent.prompt or "",
            heartbeat_prompt=agent.heartbeat_prompt or "",
            settings_yaml=agent.settings_yaml or "",
        )

        db.add(new_agent)
        await db.commit()
        await db.refresh(new_agent)

        return new_agent

    async def create_agent(self, *args, **kwargs):
        """
        Helper function to create a agent
        """
        agent_obj = await self.create_agent_db(*args, **kwargs)
        return await self.get_agent_factory(agent_obj)


agent_service = AgentService()
