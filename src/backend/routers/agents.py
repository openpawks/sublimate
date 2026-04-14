from fastapi import APIRouter, status


from schemas import AgentResponse

router = APIRouter()

# agent_home


@router.get("", response_model=list[AgentResponse])
async def get_agents_from_home():
    pass


@router.post("", response_model=AgentResponse)
async def add_agents_to_home():  # agent_home
    pass


# Agent


@router.get("", response_model=AgentResponse)
async def get_agent():
    pass


@router.put("", response_model=AgentResponse)
async def update_agent():
    pass


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent():
    """Delete agent, should also automatically delete from config file"""
    pass


# Agent Heartbeat Config
@router.get("")
async def get_agent_heartbeat_config():
    pass


@router.patch("")
async def update_agent_heartbeat_config_partial():
    pass


@router.put("")
async def update_agent_heartbeat_config_full():
    pass


# Agent State


@router.get("")  # add response_model
async def get_agent_state():
    """Get agent states (logs)"""
    pass


@router.get("")  # add response_model
async def get_agent_specific_state():
    pass


@router.detele("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_specific_state():
    pass
