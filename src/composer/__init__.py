"""
Sublimate Composer Module

This module provides the core orchestration engine for managing AI agents
in the Sublimate system.
"""

from .composer import (
    BaseTask,
    BaseAgent,
    BaseComposer,
    Heartbeat,
    HeartbeatComposer,
    PipelineComposer,
)

from .tools import (
    write_file,
    read_file,
    create_agent,
    delete_agent,
    create_task,
    close_task,
    dangerously_run_commands,
    get_all_tools,
    get_tools_by_names,
)

__all__ = [
    "BaseTask",
    "BaseAgent",
    "BaseComposer",
    "Heartbeat",
    "HeartbeatComposer",
    "PipelineComposer",
    "write_file",
    "read_file",
    "create_agent",
    "delete_agent",
    "create_task",
    "close_task",
    "dangerously_run_commands",
    "get_all_tools",
    "get_tools_by_names",
]
