from src.backend import models
from src.schemas.provider import ProviderCreate
from src.backend.database import get_db

from sqlalchemy import select


class ProviderService:
    def __init__():
        pass

    async def create_provider(self, provider: ProviderCreate):
        db = await get_db()

        db.add(
            models.Provider(
                id=provider.id, name=provider.name, api_key=provider.api_key
            )
        )

        await db.commit()
        await db.refresh()

    def get_provider(id: str):
        db = await get_db()

        provider = await db.execute(select(models.Provider.id == id)).scalars().first()

        if provider:
            return provider.model_dump()
        else:
            return None

    def remove_provider():
        # TODO:
        pass

    def update_provider_partial():
        # TODO:
        pass

    def update_provider_full():
        # TODO:
        pass
