from pydantic import BaseModel, Field


class ProviderBase(BaseModel):
    id: str = Field(
        min_length=1, max_length=50, description="User provided nickname for provider"
    )


class ProviderCreate(ProviderBase):
    name: str = Field(
        min_length=1,
        max_length=50,
        description="Actual name of the provider, eg 'deepseek', 'openai', 'ollama' or similar",
    )
    api_key: str = Field(min_length=0, max_length=50)


class ProviderUpdate(ProviderBase):
    id: str | None = Field(
        min_length=1,
        max_length=50,
        description="User provided nickname for provider",
        default=None,
    )
    name: str | None = Field(
        min_length=1,
        max_length=50,
        description="Actual name of the provider, eg 'deepseek', 'openai', 'ollama' or similar",
        default=None,
    )
    api_key: str | None = Field(min_length=0, max_length=50, default=None)
