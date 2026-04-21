from src.orchestration.agent import AgentFactory
from src.db import models
from src.db.database import get_db_session

from src.schemas.agent import AgentCreate, AgentUpdate

from sqlalchemy import select, update, delete


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

    async def get_agent_by_id(self, id: int) -> AgentFactory | None:
        """
        Get agent object by id (AgentFactory object)

        Args:
            id: agent id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Agent).where(models.Agent.id == id))
        agent_db = result.scalars().first()

        if agent_db:
            return self.get_agent_factory(agent_db)
        else:
            return None

    async def get_agents_by_project(self, project_id: int) -> list[AgentFactory]:
        """
        Get all agents for a project
        """
        db = await get_db_session()
        result = await db.execute(
            select(models.Agent).where(models.Agent.project_id == project_id)
        )
        agents = result.scalars().all()
        return [self.get_agent_factory(agent) for agent in agents]

    async def get_all_agents(self) -> list[AgentFactory]:
        """
        Get all agents
        """
        db = await get_db_session()
        result = await db.execute(select(models.Agent))
        agents = result.scalars().all()
        return [self.get_agent_factory(agent) for agent in agents]

    async def create_agent_db(
        self,
        agent: AgentCreate,
    ):
        """
        Create a new agent in the database
        """
        db = await get_db_session()

        new_agent = models.Agent(
            name=agent.name,
            project_id=agent.project_id,
            provider_id=agent.provider_id,
            model_name=agent.model_name,
            prompt=agent.prompt or "",
            heartbeat_prompt=agent.heartbeat_prompt or "",
            settings_yaml=agent.settings_yaml or "",
        )

        db.add(new_agent)
        await db.commit()
        await db.refresh(new_agent)

        return new_agent

    async def create_agent(self, agent: AgentCreate):
        """
        Helper function to create a agent
        """
        agent_obj = await self.create_agent_db(agent)
        return self.get_agent_factory(agent_obj)

    async def update_agent(
        self, id: int, agent_update: AgentUpdate
    ) -> AgentFactory | None:
        """
        Update an existing agent
        """
        db = await get_db_session()

        result = await db.execute(select(models.Agent).where(models.Agent.id == id))
        agent_db = result.scalars().first()
        if not agent_db:
            return None

        update_data = agent_update.model_dump(exclude_unset=True)

        if update_data:
            await db.execute(
                update(models.Agent).where(models.Agent.id == id).values(**update_data)
            )
            await db.commit()
            await db.refresh(agent_db)
            await db.refresh(self.get_agent_factory(agent_db).db_object)

        return self.get_agent_factory(agent_db)

    async def delete_agent(self, id: int) -> bool:
        """
        Delete an agent by id
        """
        db = await get_db_session()

        result = await db.execute(select(models.Agent).where(models.Agent.id == id))
        agent_db = result.scalars().first()
        if not agent_db:
            return False

        await db.execute(delete(models.Agent).where(models.Agent.id == id))
        await db.commit()

        if id in self.agents_in_memory:
            del self.agents_in_memory[id]

        return True


agent_service = AgentService()
