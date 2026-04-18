from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Table, Column

from database import Base

from enum import Enum


class MessageRole(Enum):
    USER = 0
    ASSISTANT = 1
    SYSTEM = 2
    OTHER = 3


# HELPER FUNCTIONS
def id_as_pk(pk=True, autoincrement=True, **kwargs):
    return mapped_column(Integer, primary_key=pk, autoincrement=autoincrement, **kwargs)


def fk(name, index=True, **kwargs):
    return mapped_column(ForeignKey(name), index=index, **kwargs)


def settings_yaml():
    return mapped_column(
        String(2048)
    )  # chose yaml, as often their format has less chars


def directory():
    return mapped_column(
        String(256)
    )  # someone can come up with a better number if they want


def nickname():
    return mapped_column(String(50), default="")


def created_at():
    return mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))


def message_content():
    return mapped_column(String(4096))


task_to_agent = Table(
    "task_to_agent",
    Base.metadata,
    Column("agent_id", ForeignKey("agents.id"), primary_key=True),
    Column("task_id", ForeignKey("tasks.id"), primary_key=True),
    Column("created_at", DateTime, default=lambda: datetime.now(UTC)),
)


class Project(Base):
    __tablename__ = "projects"

    # auto increment
    id: Mapped[int] = id_as_pk()
    name: Mapped[str] = nickname()
    user_id: Mapped[int] = fk("users.id")
    root_dir: Mapped[str] = directory()
    settings_yaml: Mapped[str] = settings_yaml()
    created_at: Mapped[datetime] = created_at()

    agents: Mapped[list[Agent]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = id_as_pk()
    name: Mapped[str] = nickname()
    project_id: Mapped[int] = fk("projects.id")
    chat_id: Mapped[int] = fk("chats.id")
    root_dir: Mapped[str] = directory()
    open: Mapped[str] = mapped_column(Boolean, default=True)

    agents: Mapped[list[Agent]] = relationship(
        secondary=task_to_agent, back_populates="agents"
    )

    created_at: Mapped[datetime] = created_at()


class Chat(Base):
    __tablename__ = "chats"

    # back populates messages
    id: Mapped[int] = id_as_pk()
    # TODO: verify this is right
    messages: Mapped[list[Message]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = created_at()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = id_as_pk()

    chat_id: Mapped[int] = fk("chats.id")
    chat: Mapped[Chat] = relationship(back_populates="messages")

    sender_id: Mapped[int] = fk("senders.id")
    sender: Mapped[Sender] = relationship(back_populates="messages")

    content: Mapped[str] = message_content()

    created_at: created_at()


class Sender(Base):
    # like "message sender" ig
    # now this is the polymorphic one !!
    __tablename__ = "senders"

    id: Mapped[int] = id_as_pk()

    messages: Mapped[list[Message]] = relationship(back_populates="sender")

    user_id: Mapped[int] = fk("users.id", nullable=True)
    user: Mapped[User] = relationship(back_populates="user")

    agent_id: Mapped[int] = fk("agents.id", nullable=True)
    agent: Mapped[Agent] = relationship(back_populates="agent")

    created_at: Mapped[datetime] = created_at()


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = id_as_pk()
    name: Mapped[str] = nickname()

    project_id: Mapped[int] = fk("projects.id")
    project: Mapped[Project] = relationship(back_populates="agents")

    model_name: Mapped[str] = nickname()

    provider_id: Mapped[str] = fk("providers.id")
    provider: Mapped[Provider] = relationship(back_populates="agents")

    settings_yaml: Mapped[str] = settings_yaml()
    prompt: Mapped[str] = message_content()
    heartbeat_prompt: Mapped[str] = message_content()  # could be half, but eh.

    tasks: Mapped[list[Task]] = relationship(
        secondary=task_to_agent, back_populates="tasks"
    )

    created_at: Mapped[datetime] = created_at()


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(
        # user provided nickname
        String(50),
        primary_key=True,
        unique=True,
    )
    name: Mapped[str] = nickname()

    api_key: Mapped[str] = nickname(nullable=True)
    kwargs: Mapped[str] = settings_yaml()

    agents: Mapped[list[Agent]] = relationship(back_populates="provider")

    created_at: Mapped[datetime] = created_at()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = id_as_pk()
    name: Mapped[str] = nickname()
    password_hash: Mapped[str] = mapped_column(String(120))

    created_at: Mapped[datetime] = created_at()
