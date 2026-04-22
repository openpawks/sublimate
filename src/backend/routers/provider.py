from fastapi import APIRouter, HTTPException, status

from ...services.provider import provider_service
from ...schemas.provider import ProviderCreate, ProviderUpdate

router = APIRouter()


def _provider_to_dict(provider) -> dict:
    return {
        "id": provider.id,
        "name": provider.name,
        "api_key": provider.api_key,
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
    }


@router.get("")
async def get_providers():
    providers = await provider_service.get_all_providers()
    return [_provider_to_dict(p) for p in providers]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_provider(new_provider: ProviderCreate):
    provider = await provider_service.create_provider(new_provider)
    if not provider:
        raise HTTPException(status_code=400, detail="Failed to create provider")
    return _provider_to_dict(provider)


@router.get("/{provider_id}")
async def get_provider(provider_id: str):
    provider = await provider_service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return _provider_to_dict(provider)


@router.patch("/{provider_id}")
async def update_provider(provider_id: str, provider_update: ProviderUpdate):
    provider = await provider_service.update_provider(provider_id, provider_update)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return _provider_to_dict(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: str):
    deleted = await provider_service.delete_provider(provider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider not found")
