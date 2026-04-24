from __future__ import annotations

from typing import Annotated, Optional

from datetime import datetime, UTC

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Table, Column

from .database import Base

from enum import Enum


class MessageRole(Enum):
    USER = 0
    ASSISTANT = 1
    SYSTEM = 2
    OTHER = 3


int_pk = Annotated[int, mapped_column(primary_key=True)]
str_50 = Annotated[str, mapped_column(String(50))]
str_100 = Annotated[str, mapped_column(String(100))]
str_256 = Annotated[str, mapped_column(String(256))]

nickname = Annotated[str, mapped_column(String(50), default="")]

message_content = Annotated[str, mapped_column(String(4096))]

settings_yaml = Annotated[Optional[str], mapped_column(String(2048), default="")]

created_at = Annotated[
    datetime,
    mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC)),
]


def fk(name, index=True, **kwargs):
    return mapped_column(ForeignKey(name), index=index, **kwargs)


task_to_agent = Table(
    "task_to_agent",
    Base.metadata,
    Column("agent_id", ForeignKey("agents.id"), primary_key=True),
    Column("task_id", ForeignKey("tasks.id"), primary_key=True),
    Column("created_at", DateTime, default=lambda: datetime.now(UTC)),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int_pk]
    name: Mapped[nickname]

    user_id: Mapped[int] = fk("users.id")
    root_dir: Mapped[str_256]
    settings_yaml: Mapped[settings_yaml]

    user: Mapped["User"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
    agents: Mapped[list["Agent"]] = relationship(back_populates="project")

    created_at: Mapped[created_at]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int_pk]
    name: Mapped[nickname]

    project_id: Mapped[int] = fk("projects.id")
    project: Mapped["Project"] = relationship(back_populates="tasks")

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", use_alter=True), nullable=True, index=True
    )
    chat: Mapped["Chat"] = relationship(foreign_keys=[chat_id], uselist=False)

    todos: Mapped[str] = mapped_column(String(512), default="")

    root_dir: Mapped[str_256]
    open: Mapped[bool] = mapped_column(Boolean, default=True)

    settings_yaml: Mapped[settings_yaml]

    agents: Mapped[list["Agent"]] = relationship(
        secondary=task_to_agent,
        back_populates="tasks",
    )

    created_at: Mapped[created_at]


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int_pk]

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", use_alter=True), nullable=True, index=True
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[created_at]


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int_pk]

    role: Mapped[str] = mapped_column(String(10), nullable=True)

    chat_id: Mapped[int] = fk("chats.id")
    chat: Mapped["Chat"] = relationship(back_populates="messages")

    sender_id: Mapped[int] = fk("senders.id", nullable=True)
    sender: Mapped["Sender"] = relationship(back_populates="messages")

    content: Mapped[message_content]

    created_at: Mapped[created_at]


class Sender(Base):
    __tablename__ = "senders"

    id: Mapped[int_pk]

    messages: Mapped[list["Message"]] = relationship(back_populates="sender")

    user_id: Mapped[int] = fk("users.id", nullable=True)
    user: Mapped["User"] = relationship(
        back_populates="senders", foreign_keys=[user_id]
    )

    agent_id: Mapped[int] = fk("agents.id", nullable=True)
    agent: Mapped["Agent"] = relationship(
        back_populates="senders", foreign_keys=[agent_id]
    )

    @property
    def sender_type(self) -> str:
        if self.agent_id:
            return "assistant"
        elif self.user_id:
            return "user"
        return "system"

    @property
    def sender_obj(self) -> "Agent | User | None":
        if self.sender_type == "assistant":
            return self.agent
        if self.sender_type == "user":
            return self.user
        return None

    created_at: Mapped[created_at]


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int_pk]
    name: Mapped[nickname]

    project_id: Mapped[int] = fk("projects.id")
    project: Mapped["Project"] = relationship(back_populates="agents")

    model_name: Mapped[nickname]

    provider_id: Mapped[str] = fk("providers.id")
    provider: Mapped["Provider"] = relationship(back_populates="agents")

    settings_yaml: Mapped[settings_yaml]

    prompt: Mapped[message_content]
    heartbeat_prompt: Mapped[str] = mapped_column(String(4096), default="")

    tasks: Mapped[list["Task"]] = relationship(
        secondary=task_to_agent,
        back_populates="agents",
    )

    senders: Mapped[list["Sender"]] = relationship(back_populates="agent")

    created_at: Mapped[created_at]


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    nickname: Mapped[str] = mapped_column(String(50), default="New provider")

    name: Mapped[nickname]
    api_key: Mapped[str] = mapped_column(String(50), nullable=True)

    agents: Mapped[list["Agent"]] = relationship(back_populates="provider")

    created_at: Mapped[created_at]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int_pk]
    name: Mapped[nickname]

    password_hash: Mapped[str] = mapped_column(String(120))

    projects: Mapped[list["Project"]] = relationship(back_populates="user")
    senders: Mapped[list["Sender"]] = relationship(back_populates="user")

    created_at: Mapped[created_at]
