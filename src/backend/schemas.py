from datetime import datetime
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    id: int
    name: str = Field(min_length=3, max_length=50)
    role: int 
    # hmmm.. don't think we should put password_hash in public facing thing...
    # token shouldn't be public facing either...
    created_at: datetime

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    pass

class ProjectBase(BaseModel):
    id: int
    root_dir: str
    agent_root_dir: str # not sure if this should be public facing...
    created_at: datetime

class ProjectCreate(BaseModel):
    pass

class ProjectResponse(BaseModel):
    pass

class MessageBase(BaseModel):
    id: int
    content: str
    created_at: datetime

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    pass

class ChatBase(BaseModel):
    id: int
    created_at: datetime

class ChatCreate(ChatBase):
    pass 

class ChatResponse(ChatBase):
    pass 

class TaskBase(BaseModel):
    id: int
    project_id: int
    chat_id: int

class TastCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    pass
