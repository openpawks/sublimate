from fastapi import APIRouter, HTTPException, status

from ...services.agent import agent_service
from ...schemas.agent import AgentCreate, AgentUpdate

router = APIRouter()


def _agent_to_dict(agent) -> dict:
    db = agent.db_object
    return {
        "id": db.id,
        "name": db.name,
        "project_id": db.project_id,
        "provider_id": db.provider_id,
        "model_name": db.model_name,
        "prompt": db.prompt,
        "heartbeat_prompt": db.heartbeat_prompt,
        "settings_yaml": db.settings_yaml,
        "created_at": db.created_at.isoformat() if db.created_at else None,
    }


@router.get("")
async def get_agents(project_id: int | None = None):
    if project_id is not None:
        agents = await agent_service.get_agents_by_project(project_id)
    else:
        agents = await agent_service.get_all_agents()
    return [_agent_to_dict(a) for a in agents]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(new_agent: AgentCreate):
    agent = await agent_service.create_agent(new_agent)
    if not agent:
        raise HTTPException(status_code=400, detail="Failed to create agent")
    return _agent_to_dict(agent)


@router.get("/{agent_id}")
async def get_agent(agent_id: int):
    agent = await agent_service.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.patch("/{agent_id}")
async def update_agent(agent_id: int, agent_update: AgentUpdate):
    agent = await agent_service.update_agent(agent_id, agent_update)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int):
    deleted = await agent_service.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
