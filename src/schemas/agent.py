from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="agent nickname")
    project_id: int
    provider_id: str = Field(
        min_length=1,
        max_length=50,
        description="nickname of provider that the user has assigned for provider",
    )
    prompt: str | None = Field(
        min_length=0, max_length=4096, description="prompt for agent"
    )
    heartbeat_prompt: str | None = Field(
        min_length=0, max_length=4096, description="heartbeat_prompt for agent"
    )
    settings_yaml: str | None = Field(
        min_length=0, max_length=4096, description="optional settings in yaml format"
    )


class AgentCreate(AgentBase):
    pass
