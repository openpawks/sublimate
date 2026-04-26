from pydantic import BaseModel
from datetime import datetime
import re


def is_filesafe(name: str) -> bool:
    """
    Check if a string is safe for use as a filename/branch name.
    Allows alphanumeric, hyphens, underscores, dots, no spaces or slashes.
    """
    pattern = r"^[a-zA-Z0-9_.-]+$"
    return bool(re.match(pattern, name))


def to_filesafe(name: str) -> str:
    """
    Convert a string to be safe for use as a filename/branch name.
    Replaces invalid characters (spaces, slashes, etc.) with hyphens.
    """
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", name)
    safe = re.sub(r"-+", "-", safe)
    safe = safe.strip("-.")
    return safe if safe else "unnamed"


class ProjectData(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    user_id: int
    root_dir: str
    settings_yaml: str | None
    created_at: datetime


class TaskData(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    project_id: int
    chat_id: int | None
    todos: str
    root_dir: str
    open: bool
    settings_yaml: str | None
    created_at: datetime


class ChatData(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    task_id: int | None
    created_at: datetime


class AgentData(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    project_id: int
    provider_id: str
    model_name: str
    prompt: str
    heartbeat_prompt: str
    settings_yaml: str | None
    created_at: datetime


class ProviderData(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    nickname: str
    name: str
    api_key: str
    settings_yaml: str
    created_at: datetime


class MessageData(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    role: str
    chat_id: int
    content: str
    created_at: datetime
