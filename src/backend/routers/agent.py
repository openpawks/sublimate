from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated

from ...services.agent import agent_service
from ...schemas.agent import AgentCreate, AgentUpdate

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db_session

router = APIRouter()


def _agent_to_dict(agent) -> dict:
    d = agent._data
    return {
        "id": d.id,
        "name": d.name,
        "project_id": d.project_id,
        "provider_id": d.provider_id,
        "model_name": d.model_name,
        "prompt": d.prompt,
        "heartbeat_prompt": d.heartbeat_prompt,
        "settings_yaml": d.settings_yaml,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("")
async def get_agents(
    db: Annotated[AsyncSession, Depends(get_db_session)], project_id: int | None = None
):
    if project_id is not None:
        agents = await agent_service.get_agents_by_project(project_id, db)
    else:
        agents = await agent_service.get_all_agents(db)
    return [_agent_to_dict(a) for a in agents]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(
    new_agent: AgentCreate, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    agent = await agent_service.create_agent(new_agent, db)
    if not agent:
        raise HTTPException(status_code=400, detail="Failed to create agent")
    return _agent_to_dict(agent)


@router.get("/{agent_id}")
async def get_agent(
    agent_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    agent = await agent_service.get_agent_by_id(agent_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    agent = await agent_service.update_agent(agent_id, agent_update, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    deleted = await agent_service.delete_agent(agent_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
