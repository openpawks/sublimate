from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
    CheckpointTuple,
)

from collections.abc import Sequence, AsyncIterator

from sqlalchemy import select, delete


def _extract_messages_from_checkpoint(checkpoint: Checkpoint) -> list[dict]:
    """
    Extract and format messages from a checkpoint's channel values.

    Converts LangChain message objects or dictionaries into a standardized format
    with 'role' and 'content' fields. Handles tool calls by converting them to
    text representations.

    Args:
        checkpoint: The checkpoint containing messages in channel_values

    Returns:
        List of dictionaries with 'role' and 'content' keys, formatted for database storage
    """
    messages = checkpoint.get("channel_values", {}).get("messages", [])
    result = []
    for msg in messages:
        if hasattr(msg, "type"):
            role_map = {
                "human": "user",
                "ai": "assistant",
                "system": "system",
                "tool": "system",
                "function": "assistant",
            }
            role = role_map.get(msg.type, "user")
            content = str(msg.content) if msg.content else ""

            tool_calls = getattr(msg, "tool_calls", None) or []
            if tool_calls:
                parts = [content] if content else []
                for tc in tool_calls:
                    parts.append(
                        f"[Tool Call: {tc.get('name', 'unknown')}({tc.get('args', {})})]"
                    )
                content = "\n".join(parts)

            result.append({"role": role, "content": content})
        elif isinstance(msg, dict):
            role_map = {
                "human": "user",
                "ai": "assistant",
                "system": "system",
                "tool": "system",
            }
            role = role_map.get(msg.get("type", ""), "user")
            content = str(msg.get("content", ""))

            tool_calls = msg.get("tool_calls", None) or []
            if tool_calls:
                parts = [content] if content else []
                for tc in tool_calls:
                    parts.append(
                        f"[Tool Call: {tc.get('name', 'unknown')}({tc.get('args', {})})]"
                    )
                content = "\n".join(parts)

            result.append({"role": role, "content": content})
    return result


def _get_chat_id_from_thread_id(thread_id: str) -> int | None:
    """
    Convert a thread ID string to an integer chat ID.

    Args:
        thread_id: The thread ID string to convert

    Returns:
        Integer chat ID if conversion succeeds, None otherwise
    """
    try:
        return int(thread_id)
    except (ValueError, TypeError):
        return None


class MyCheckpointer(BaseCheckpointSaver):
    """
    A custom checkpoint saver for LangGraph that persists checkpoints to a SQL database.

    This checkpoint saver integrates with the application's database to store and retrieve
    checkpoint states. It automatically syncs messages from checkpoints to the message
    service and manages checkpoint state records with parent-child relationships.

    The checkpointer uses thread_id as the primary identifier for conversation threads
    and maintains checkpoint metadata including timestamps and parent references.
    """

    def __init__(self):
        """Initialize the checkpoint saver with base class initialization."""
        super().__init__()

    async def __aenter__(self):
        """Async context manager entry method."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit method."""
        return False

    def _get_thread_id(self, config: RunnableConfig) -> str:
        """
        Extract the thread ID from a runnable configuration.

        Args:
            config: Runnable configuration containing thread_id in configurable dict

        Returns:
            The thread ID string
        """
        return config["configurable"]["thread_id"]

    async def _sync_messages(self, config: RunnableConfig, checkpoint: Checkpoint):
        """
        Synchronize messages from a checkpoint to the database.

        Extracts messages from the checkpoint and saves them to the database using
        the message service. Prevents duplicate messages by checking existing messages
        based on role and content combination.

        Args:
            config: Runnable configuration containing thread_id
            checkpoint: Checkpoint containing messages to sync
        """
        from src.db.database import get_db_session
        from src.schemas.message import MessageCreate
        from src.schemas.data import MessageData
        from src.services.registry import registry

        thread_id = self._get_thread_id(config)
        chat_id = _get_chat_id_from_thread_id(thread_id)
        if chat_id is None:
            return

        messages = _extract_messages_from_checkpoint(checkpoint)
        if not messages:
            return

        db = await get_db_session()

        messages_to_create = []

        chat_messages = [
            MessageData.model_validate(m)
            for m in await registry.message_service.get_messages_by_chat(
                chat_id=chat_id, db=db
            )
        ]

        chat_messages_hashmap = {f"{m.role}{m.content}" for m in chat_messages}

        for msg in messages:
            if len(msg["content"]) > 4096:
                # TODO: split into multiple messages
                # OR truncate it
                continue

            if f"{msg['role']}{msg['content']}" in chat_messages_hashmap:
                continue

            messages_to_create.append(
                MessageCreate(content=msg["content"], role=msg["role"], chat_id=chat_id)
            )

        await registry.message_service.create_messages(
            messages=messages_to_create, db=db
        )

        await db.commit()

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """
        Save a checkpoint asynchronously.

        Stores the checkpoint state in the database. If a checkpoint with the same
        ID already exists, it is deleted before creating the new one. Also syncs
        messages from the checkpoint to the message service.

        Args:
            config: Runnable configuration with thread_id and optionally checkpoint_ns
            checkpoint: The checkpoint data to save
            metadata: Metadata associated with the checkpoint
            new_versions: Channel version information (unused in this implementation)

        Returns:
            RunnableConfig containing the updated configuration with checkpoint_id
        """
        from src.db.database import get_db_session
        from src.db.models import CheckpointState

        thread_id = self._get_thread_id(config)
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        await self._sync_messages(config, checkpoint)

        db = await get_db_session()
        existing = await db.execute(
            select(CheckpointState).where(
                CheckpointState.thread_id == thread_id,
                CheckpointState.checkpoint_ns == checkpoint_ns,
                CheckpointState.checkpoint_id == checkpoint_id,
            )
        )
        if existing.scalars().first():
            await db.execute(
                delete(CheckpointState).where(
                    CheckpointState.thread_id == thread_id,
                    CheckpointState.checkpoint_ns == checkpoint_ns,
                    CheckpointState.checkpoint_id == checkpoint_id,
                )
            )

        record = CheckpointState(
            thread_id=thread_id,
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint_id,
            parent_checkpoint_id=parent_checkpoint_id,
            checkpoint=checkpoint,
            checkpoint_metadata=metadata,
            pending_writes=None,
        )
        db.add(record)
        await db.commit()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aget(self, config: RunnableConfig) -> Checkpoint | None:
        """
        Retrieve a checkpoint asynchronously.

        Fetches a checkpoint by its configuration. If no checkpoint_id is specified,
        returns the most recent checkpoint for the thread.

        Args:
            config: Runnable configuration with thread_id and optional checkpoint_id

        Returns:
            The requested Checkpoint object, or None if not found
        """
        from src.db.database import get_db_session
        from src.db.models import CheckpointState

        thread_id = self._get_thread_id(config)
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        db = await get_db_session()
        query = select(CheckpointState).where(
            CheckpointState.thread_id == thread_id,
            CheckpointState.checkpoint_ns == checkpoint_ns,
        )

        if checkpoint_id:
            query = query.where(CheckpointState.checkpoint_id == checkpoint_id)
        else:
            query = query.order_by(CheckpointState.created_at.desc()).limit(1)

        result = await db.execute(query)
        record = result.scalars().first()

        if record:
            return Checkpoint(**record.checkpoint)
        return None

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """
        Retrieve a checkpoint tuple asynchronously.

        Fetches a checkpoint along with its configuration, metadata, parent reference,
        and pending writes. Parent configuration is automatically resolved if
        parent_checkpoint_id exists.

        Args:
            config: Runnable configuration with thread_id and optional checkpoint_id

        Returns:
            CheckpointTuple containing checkpoint data and metadata, or None if not found
        """
        from src.db.database import get_db_session
        from src.db.models import CheckpointState

        thread_id = self._get_thread_id(config)
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        db = await get_db_session()
        query = select(CheckpointState).where(
            CheckpointState.thread_id == thread_id,
            CheckpointState.checkpoint_ns == checkpoint_ns,
        )

        if checkpoint_id:
            query = query.where(CheckpointState.checkpoint_id == checkpoint_id)
        else:
            query = query.order_by(CheckpointState.created_at.desc()).limit(1)

        result = await db.execute(query)
        record = result.scalars().first()

        if record:
            parent_config = None
            if record.parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": record.parent_checkpoint_id,
                    }
                }

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": record.checkpoint_id,
                    }
                },
                checkpoint=Checkpoint(**record.checkpoint),
                metadata=CheckpointMetadata(**record.checkpoint_metadata),
                parent_config=parent_config,
                pending_writes=record.pending_writes,
            )
        return None

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """
        List checkpoints asynchronously.

        Returns an async iterator of checkpoint tuples for a thread, ordered by creation
        time descending. Supports filtering by metadata, limiting results, and listing
        only checkpoints before a specific checkpoint.

        Args:
            config: Runnable configuration with thread_id (or None for no results)
            filter: Optional dictionary of metadata key-value pairs to filter by
            before: Optional configuration specifying a checkpoint to list before
            limit: Maximum number of checkpoints to return

        Yields:
            CheckpointTuple objects matching the query criteria
        """
        from src.db.database import get_db_session
        from src.db.models import CheckpointState

        if config is None:
            return

        thread_id = self._get_thread_id(config)
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        db = await get_db_session()

        before_ts = None
        if before and before.get("configurable", {}).get("checkpoint_id"):
            before_id = before["configurable"]["checkpoint_id"]
            before_result = await db.execute(
                select(CheckpointState.created_at).where(
                    CheckpointState.thread_id == thread_id,
                    CheckpointState.checkpoint_ns == checkpoint_ns,
                    CheckpointState.checkpoint_id == before_id,
                )
            )
            before_ts = before_result.scalar()

        query = (
            select(CheckpointState)
            .where(
                CheckpointState.thread_id == thread_id,
                CheckpointState.checkpoint_ns == checkpoint_ns,
            )
            .order_by(CheckpointState.created_at.desc())
        )

        result = await db.execute(query)
        records = result.scalars().all()

        count = 0
        for record in records:
            if before_ts and record.created_at >= before_ts:
                continue

            if filter:
                md = record.checkpoint_metadata or {}
                match = True
                for key, value in filter.items():
                    if md.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            parent_config = None
            if record.parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": record.parent_checkpoint_id,
                    }
                }

            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": record.checkpoint_id,
                    }
                },
                checkpoint=Checkpoint(**record.checkpoint),
                metadata=CheckpointMetadata(**record.checkpoint_metadata),
                parent_config=parent_config,
                pending_writes=record.pending_writes,
            )

            count += 1
            if limit and count >= limit:
                break

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """
        Save pending writes for a checkpoint asynchronously.

        Stores writes (channel updates) that are pending for a checkpoint. Prevents
        duplicate writes by checking existing pending writes for the same task_id,
        channel, and value combination.

        Args:
            config: Runnable configuration with thread_id and checkpoint_id
            writes: Sequence of (channel, value) tuples to save
            task_id: Identifier for the task creating these writes
            task_path: Optional path information for the task (unused)
        """
        from src.db.database import get_db_session
        from src.db.models import CheckpointState

        thread_id = self._get_thread_id(config)
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        db = await get_db_session()
        result = await db.execute(
            select(CheckpointState).where(
                CheckpointState.thread_id == thread_id,
                CheckpointState.checkpoint_ns == checkpoint_ns,
                CheckpointState.checkpoint_id == checkpoint_id,
            )
        )
        record = result.scalars().first()

        if record:
            existing = list(record.pending_writes) if record.pending_writes else []
            for channel, value in writes:
                dup = False
                for ew in existing:
                    if (
                        len(ew) >= 3
                        and ew[0] == task_id
                        and ew[1] == channel
                        and ew[2] == value
                    ):
                        dup = True
                        break
                if not dup:
                    existing.append((task_id, channel, value))
            record.pending_writes = existing
            await db.commit()

    async def adelete_thread(
        self,
        thread_id: str,
    ) -> None:
        """
        Delete all checkpoints for a thread asynchronously.

        Removes all checkpoint states associated with the given thread_id from the database.

        Args:
            thread_id: The thread identifier whose checkpoints should be deleted
        """
        from src.db.database import get_db_session
        from src.db.models import CheckpointState

        db = await get_db_session()
        await db.execute(
            delete(CheckpointState).where(CheckpointState.thread_id == thread_id)
        )
        await db.commit()


checkpointer = MyCheckpointer()
