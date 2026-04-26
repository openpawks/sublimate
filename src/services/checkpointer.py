from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
    # empty_checkpoint,
    # copy_checkpoint,
)

from collections.abc import Sequence

import contextlib


class MyCheckpointer(BaseCheckpointSaver):
    def __init__(self):
        super().__init__()

    async def __aenter__(self):
        # Setup/acquire resource
        # print("Acquiring resource...")
        # await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup/release resource
        # print("Releasing resource...")
        # await self.disconnect()
        # Return True if you handled the exception
        return False

    @contextlib.asynccontextmanager
    async def aget(self, config: RunnableConfig):
        # Your custom logic to create a connection pool and initialize your checkpointer here.
        pass

    @contextlib.asynccontextmanager
    async def aget_tuple(self, config: RunnableConfig):
        pass

    @contextlib.asynccontextmanager
    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ):
        pass

    @contextlib.asynccontextmanager
    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        pass

    @contextlib.asynccontextmanager
    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        pass

    @contextlib.asynccontextmanager
    async def adelete_thread(
        self,
        thread_id: str,
    ) -> None:
        pass


checkpointer = MyCheckpointer()
