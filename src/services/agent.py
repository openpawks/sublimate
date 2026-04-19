from src.orchestration.agent import AgentFactory
from src.backend import models
from src.backend.database import get_db

from sqlalchemy import select


class AgentService:
    def __init__(self):
        self.agents_in_memory = {}

    def get_base_agent_by_id(self, id: int):
        """
        Get AgentFactory by id, from memory

        Args:
            id: agent id
        """
        return self.agents_in_memory.get(id)

    def get_base_agent(self, db_object: models.Agent):
        """
        Load AgentFactory into memory
        """
        agent = self.agents_in_memory.get(id)
        if agent:
            return agent

        self.agents_in_memory[id] = AgentFactory(
            db_object=db_object,
        )

        return self.agents_in_memory.get(id)

    def get_agent_by_id(self, id: int) -> AgentFactory:
        """
        Get agent object by id (AgentFactory object)

        Args:
            id: agent id
        """
        db = await get_db()

        agent_db = await db.execute(select(models.Agent.id == id)).scalars().first()

        if agent_db:
            return self.get_base_agent(agent_db)
        else:
            return None

    async def create_agent_db(
        self,
        name: str,
        project_id: int,
        root_dir: str,
        settings_yaml: str = "",
    ):
        """
        Create a new agent in the database

        Args:
            name: name of the agent
            project_id: id of parent project
            root_dir: worktree root directory
            settings_yaml: optional extra settings
        """
        db = await get_db()

        new_agent = models.Agent(
            name=name,
            project_id=project_id,
            root_dir=root_dir,
            settings_yaml=settings_yaml,
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
        return await self.get_base_agent(agent_obj)


agent_service = AgentService()
