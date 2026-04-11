from datetime import datetime
from pydantic import BaseModel, Field


# USER MANAGEMENT
class UserBase(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: int
    # hmmm.. don't think we should put password_hash in public facing thing...
    # token shouldn't be public facing either...


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    created_at: datetime


# FILE
class TextFileContents(BaseModel):
    content: str


# PROJECT MANAGEMENT
class ProjectBase(BaseModel):
    # TODO: project name?
    root_dir: str
    agent_root_dir: str  # not sure if this should be public facing...


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    created_at: datetime


class ProjectUpdate(ProjectBase):
    root_dir: str | None
    agent_root_dir: str | None


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    created_at: datetime


class ChatBase(BaseModel):
    pass


class ChatCreate(ChatBase):
    pass


class ChatResponse(ChatBase):
    created_at: datetime


class TaskBase(BaseModel):
    pass


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    chat_id: int
    project_id: int
    created_at: datetime


class HeartbeatBase(BaseModel):
    cron: str
    dependencies: list[str]
    content: str




class AgentCreate(BaseModel):
    pass

class AgentUpdate(BaseModel):
    pass 

class AgentResponse(BaseModel):
    pass 


