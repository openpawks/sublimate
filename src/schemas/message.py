from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    chat_id: int


class MessageCreate(MessageBase):
    content: str = Field(
        max_length=4096,
        min_length=1,
    )
    role: str = Field(
        max_length=10,
        min_length=0,
    )


class MessageUpdate(MessageBase):
    content: str | None = Field(
        max_length=4096,
        min_length=1,
    )
    role: str | None = Field(
        max_length=10,
        min_length=0,
    )
