from pydantic import BaseModel, Field


class ProviderBase(BaseModel):
    id: str = Field(
        min_length=1, max_length=50, description="User provided nickname for provider"
    )
    name: str = Field(
        min_length=1,
        max_length=50,
        description="Actual name of the provider, eg 'deepseek', 'openai', 'ollama' or similar",
    )
    api_key: str(min_length=0, max_length=50)


class ProviderCreate(ProviderBase):
    pass
