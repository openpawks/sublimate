from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="agent nickname")
    project_id: int
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
    provider_id: str = Field(
        min_length=1,
        max_length=50,
        description="Nickname of provider that the user has assigned for provider",
    )
    model_name: str = Field(
        min_length=1,
        max_length=50,
        description="Name of the model, such as 'deepseek-reasoner', 'gpt-5', 'qwen3.5:9b'",
    )


class AgentUpdate(AgentBase):
    provider_id: str | None = Field(
        min_length=1,
        max_length=50,
        description="nickname of provider that the user has assigned for provider",
    )
    model_name: str | None = Field(
        min_length=1,
        max_length=50,
        description="Name of the model, such as 'deepseek-reasoner', 'gpt-5', 'qwen3.5:9b'",
    )
