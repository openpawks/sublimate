"""
Tools for Sublimate agents.

This module provides tools that agents can use to interact with the filesystem,
manage tasks, and perform other operations. Tools are implemented as LangChain
tools that can be used with the agent system.
"""

from pathlib import Path
import os
import subprocess
import json
import functools
from typing import Optional, Dict, Any, Callable
from datetime import datetime

# Try to import LangChain tools, but provide fallback for testing
_HAS_LANGCHAIN = True
try:
    from langchain.tools import BaseTool
    from langchain.tools.base import StructuredTool
    from langchain.tools import tool as langchain_tool_decorator
except ImportError:
    _HAS_LANGCHAIN = False

    # Create mock classes for when langchain is not available
    class BaseTool:
        """Mock BaseTool for when langchain is not available."""

        pass

    class StructuredTool(BaseTool):
        """Mock StructuredTool for when langchain is not available."""

        @staticmethod
        def from_function(func: Callable, **kwargs):
            """Mock from_function method."""
            return func

    # Mock decorator
    def langchain_tool_decorator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


def _create_tool(
    func: Callable, name: Optional[str] = None, description: Optional[str] = None
) -> Any:
    """
    Create a LangChain tool from a function.

    Args:
        func: The function to wrap as a tool
        name: Optional name for the tool (defaults to function name)
        description: Optional description (defaults to function docstring)

    Returns:
        A LangChain tool object or the original function if LangChain is not available
    """
    if not _HAS_LANGCHAIN:
        return func

    # Use StructuredTool.from_function to create a tool
    tool_name = name or func.__name__
    tool_description = description or (func.__doc__ or "")

    # Clean up description - take first line if multi-line
    if "\n" in tool_description:
        tool_description = tool_description.split("\n")[0]

    return StructuredTool.from_function(
        func=func,
        name=tool_name,
        description=tool_description,
    )


def write_file(file_path: str, content: str, append: bool = False) -> str:
    """
    Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        append: If True, append to the file instead of overwriting

    Returns:
        Success message or error description
    """
    try:
        path = Path(file_path)

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to {file_path}: {str(e)}"


def read_file(file_path: str) -> str:
    """
    Read content from a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File content or error message
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"File not found: {file_path}"

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return content
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"


def create_agent(
    name: str,
    agent_type: str = "coder",
    model: str = "default",
    description: str = "",
    tools: Optional[list] = None,
) -> str:
    """
    Create a new agent configuration.

    Args:
        name: Name of the agent
        agent_type: Type of agent (coder, tester, reviewer, etc.)
        model: Model to use for the agent
        description: Description of the agent's role
        tools: List of tools the agent can use

    Returns:
        Success message or error description
    """
    try:
        if tools is None:
            tools = ["read_file", "write_file"]

        agent_config = {
            "name": name,
            "type": agent_type,
            "model": model,
            "description": description,
            "tools": tools,
            "created_at": datetime.now().isoformat(),
        }

        # In a real implementation, this would write to a database
        # or create configuration files
        config_str = json.dumps(agent_config, indent=2)

        return f"Created agent '{name}' of type '{agent_type}' with model '{model}'. Configuration:\n{config_str}"
    except Exception as e:
        return f"Error creating agent: {str(e)}"


def delete_agent(name: str) -> str:
    """
    Delete an agent configuration.

    Args:
        name: Name of the agent to delete

    Returns:
        Success message or error description
    """
    try:
        # In a real implementation, this would delete from a database
        # or remove configuration files
        return (
            f"Agent '{name}' marked for deletion. (Note: This is a mock implementation)"
        )
    except Exception as e:
        return f"Error deleting agent: {str(e)}"


def create_task(
    title: str,
    description: str,
    agent: Optional[str] = None,
    priority: str = "medium",
    tags: Optional[list] = None,
) -> str:
    """
    Create a new task for agents to work on.

    Args:
        title: Title of the task
        description: Detailed description of the task
        agent: Optional agent to assign the task to
        priority: Priority level (low, medium, high, critical)
        tags: Optional list of tags for the task

    Returns:
        Task ID or error description
    """
    try:
        if tags is None:
            tags = []

        # Generate a simple task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        task_data = {
            "id": task_id,
            "title": title,
            "description": description,
            "agent": agent,
            "priority": priority,
            "tags": tags,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # In a real implementation, this would write to a database
        task_str = json.dumps(task_data, indent=2)

        return f"Created task '{title}' with ID {task_id}:\n{task_str}"
    except Exception as e:
        return f"Error creating task: {str(e)}"


def close_task(task_id: str, notes: str = "") -> str:
    """
    Close a task, marking it as complete.

    Args:
        task_id: ID of the task to close
        notes: Optional notes about the completion

    Returns:
        Success message or error description
    """
    try:
        # In a real implementation, this would update a database
        return f"Task {task_id} closed. Notes: {notes}"
    except Exception as e:
        return f"Error closing task: {str(e)}"


def dangerously_run_commands(command: str, timeout: int = 30) -> str:
    """
    Run shell commands. WARNING: This is dangerous and should be used with caution.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds

    Returns:
        Command output or error message
    """
    try:
        # IMPORTANT: In a production system, this should have extensive
        # security controls, sandboxing, and permission checks

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )

        output = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command,
        }

        return json.dumps(output, indent=2)
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds: {command}"
    except Exception as e:
        return f"Error running command: {str(e)}"


# Create LangChain tool objects from the functions
write_file_tool = _create_tool(write_file)
read_file_tool = _create_tool(read_file)
create_agent_tool = _create_tool(create_agent)
delete_agent_tool = _create_tool(delete_agent)
create_task_tool = _create_tool(create_task)
close_task_tool = _create_tool(close_task)
dangerously_run_commands_tool = _create_tool(
    dangerously_run_commands,
    description="Run shell commands. WARNING: This is dangerous and should be used with caution.",
)


# Utility function to get all tools as LangChain tool objects
def get_all_tools() -> Dict[str, Any]:
    """
    Get a dictionary of all available tools as LangChain tool objects.

    Returns:
        Dictionary mapping tool names to LangChain tool objects
    """
    tools = {
        "write_file": write_file_tool,
        "read_file": read_file_tool,
        "create_agent": create_agent_tool,
        "delete_agent": delete_agent_tool,
        "create_task": create_task_tool,
        "close_task": close_task_tool,
        "dangerously_run_commands": dangerously_run_commands_tool,
    }
    return tools


# Utility function to get tools by names
def get_tools_by_names(tool_names: list) -> Dict[str, Any]:
    """
    Get a dictionary of tools filtered by names.

    Args:
        tool_names: List of tool names to include

    Returns:
        Dictionary mapping tool names to tool objects
    """
    all_tools = get_all_tools()
    return {name: all_tools[name] for name in tool_names if name in all_tools}


# Also export the raw functions for direct use
__all__ = [
    "write_file",
    "read_file",
    "create_agent",
    "delete_agent",
    "create_task",
    "close_task",
    "dangerously_run_commands",
    "write_file_tool",
    "read_file_tool",
    "create_agent_tool",
    "delete_agent_tool",
    "create_task_tool",
    "close_task_tool",
    "dangerously_run_commands_tool",
    "get_all_tools",
    "get_tools_by_names",
]
