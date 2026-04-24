from src.orchestration.agent import AgentFactory
from src.db import models

from src.schemas.agent import AgentCreate, AgentUpdate
from src.schemas.data import AgentData

from sqlalchemy import select, update, delete

from sqlalchemy.ext.asyncio import AsyncSession


class AgentService:
    def __init__(self):
        self.agents_in_memory = {}

    def get_agent_factory_by_id(self, id: int):
        return self.agents_in_memory.get(id)

    def get_or_create_agent_factory(self, data: AgentData):
        agent = self.agents_in_memory.get(data.id)
        if agent:
            return agent

        self.agents_in_memory[data.id] = AgentFactory(
            data=data,
        )

        return self.agents_in_memory.get(data.id)

    async def get_agent_by_id(self, id: int, db: AsyncSession) -> AgentFactory | None:
        result = await db.execute(select(models.Agent).where(models.Agent.id == id))
        agent_db = result.scalars().first()

        if agent_db:
            data = AgentData.model_validate(agent_db)
            return self.get_or_create_agent_factory(data)
        else:
            return None

    async def get_agents_by_project(
        self, project_id: int, db: AsyncSession
    ) -> list[AgentFactory]:
        result = await db.execute(
            select(models.Agent).where(models.Agent.project_id == project_id)
        )
        agents = result.scalars().all()
        return [
            self.get_or_create_agent_factory(AgentData.model_validate(a))
            for a in agents
        ]

    async def get_all_agents(self, db: AsyncSession) -> list[AgentFactory]:
        result = await db.execute(select(models.Agent))
        agents = result.scalars().all()
        return [
            self.get_or_create_agent_factory(AgentData.model_validate(a))
            for a in agents
        ]

    async def create_agent_db(self, agent: AgentCreate, db: AsyncSession):
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

    async def create_agent(self, agent: AgentCreate, db: AsyncSession):
        agent_obj = await self.create_agent_db(agent, db)
        data = AgentData.model_validate(agent_obj)
        return self.get_or_create_agent_factory(data)

    async def update_agent(
        self, id: int, agent_update: AgentUpdate, db: AsyncSession
    ) -> AgentFactory | None:
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

        agent = self.get_agent_factory_by_id(id)
        if agent:
            agent._data = AgentData.model_validate(agent_db)

        return self.get_agent_factory_by_id(id) or self.get_or_create_agent_factory(
            AgentData.model_validate(agent_db)
        )

    async def delete_agent(self, id: int, db: AsyncSession) -> bool:
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
