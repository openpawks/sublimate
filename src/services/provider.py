from src.db import models
from src.schemas.provider import ProviderCreate, ProviderUpdate
from src.db.database import get_db_session

from sqlalchemy import select, update, delete


class ProviderService:
    def __init__(self):
        pass

    async def create_provider(self, provider: ProviderCreate):
        db = await get_db_session()

        new_provider = models.Provider(
            id=provider.id, name=provider.name, api_key=provider.api_key
        )
        db.add(new_provider)

        await db.commit()
        await db.refresh(new_provider)
        return new_provider

    async def get_provider(self, id: str):
        db = await get_db_session()

        result = await db.execute(
            select(models.Provider).where(models.Provider.id == id)
        )
        provider = result.scalars().first()

        if provider:
            return provider
        else:
            return None

    async def get_all_providers(self):
        db = await get_db_session()
        result = await db.execute(select(models.Provider))
        providers = result.scalars().all()
        return providers

    async def update_provider(self, id: str, provider_update: ProviderUpdate):
        db = await get_db_session()

        result = await db.execute(
            select(models.Provider).where(models.Provider.id == id)
        )
        provider = result.scalars().first()
        if not provider:
            return None

        update_data = provider_update.model_dump(exclude_unset=True)
        # Remove id from update data as primary key should not be changed
        update_data.pop("id", None)

        if update_data:
            await db.execute(
                update(models.Provider)
                .where(models.Provider.id == id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(provider)
            # TODO: reset associated AgentFactorys and WorkerAgents and ChatAgents
            # this may be somewhat complicated
            # but you can do select by provider_id for this, then use agent_service to update the agents

        return provider

    async def delete_provider(self, id: str) -> bool:
        db = await get_db_session()

        result = await db.execute(
            select(models.Provider).where(models.Provider.id == id)
        )
        provider = result.scalars().first()
        if not provider:
            return False

        await db.execute(delete(models.Provider).where(models.Provider.id == id))
        await db.commit()
        return True


provider_service = ProviderService()
