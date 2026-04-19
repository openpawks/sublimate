from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    content: str = Field(
        max_length=4096,
        min_length=1,
    )
    chat_id: int


class MessageCreate(MessageBase):
    role: str = Field(
        max_length=10,
        min_length=0,
    )
