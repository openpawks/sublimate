"""
Tools for Sublimate agents.

This module provides tools that agents can use to interact with the filesystem,
manage tasks, and perform other operations. Tools are implemented as LangChain
tools that can be used with the agent system.
"""

from pathlib import Path
import subprocess
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import glob
import re

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

    # Ensure description is not empty
    if not tool_description:
        tool_description = "Tool function."

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


def read_file_lines(
    file_path: str, start_line: int = 1, end_line: Optional[int] = None
) -> str:
    """
    Read specific lines from a file.

    Args:
        file_path: Path to the file to read
        start_line: First line to read (1-indexed, inclusive)
        end_line: Last line to read (1-indexed, inclusive). If None, reads to end of file.

    Returns:
        Requested lines as a string, or error message
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"File not found: {file_path}"

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Validate line numbers
        total_lines = len(lines)
        if start_line < 1:
            start_line = 1
        if start_line > total_lines:
            return f"Start line {start_line} exceeds file length ({total_lines} lines)"

        if end_line is None:
            end_line = total_lines
        elif end_line < start_line:
            # If end_line is less than start_line, swap them
            start_line, end_line = end_line, start_line
        if end_line > total_lines:
            end_line = total_lines

        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line  # exclusive slice
        selected_lines = lines[start_idx:end_idx]

        # Join lines, preserving original newlines
        content = "".join(selected_lines)
        return content
    except Exception as e:
        return f"Error reading lines from {file_path}: {str(e)}"


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


def insert_file_lines(file_path: str, content: str, line_number: int) -> str:
    """
    Insert content at a specific line number in a file.

    Args:
        file_path: Path to the file
        content: Content to insert
        line_number: Line number to insert before (1-indexed). If line_number
                     exceeds total lines, content is appended.

    Returns:
        Success message or error description
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"File not found: {file_path}"

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Convert line_number to 0-indexed
        idx = line_number - 1
        if idx < 0:
            idx = 0
        if idx > len(lines):
            idx = len(lines)

        # Split content into lines, preserving newline characters
        new_lines = content.splitlines(keepends=True)
        if not new_lines:
            new_lines = [""]

        # Insert or append
        lines[idx:idx] = new_lines

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return f"Successfully inserted content at line {line_number} in {file_path}"
    except Exception as e:
        return f"Error inserting content in {file_path}: {str(e)}"


def glob_files(pattern: str, path: Optional[str] = None) -> str:
    """
    Find files matching a glob pattern.

    Args:
        pattern: Glob pattern to match
        path: Optional directory to search in (defaults to current directory)

    Returns:
        JSON list of matched file paths or error message
    """
    try:
        search_path = path if path else "."
        # Use glob.glob with recursive pattern support
        matches = glob.glob(pattern, root_dir=search_path, recursive=True)
        # Convert to absolute paths
        abs_matches = [str(Path(search_path) / m) for m in matches]
        return json.dumps(abs_matches, indent=2)
    except Exception as e:
        return f"Error globbing pattern {pattern}: {str(e)}"


def grep_files(
    pattern: str, path: Optional[str] = None, include: Optional[str] = None
) -> str:
    """
    Search for pattern in files.

    Args:
        pattern: Regex pattern to search for
        path: Optional directory to search in (defaults to current directory)
        include: Optional file pattern to include (e.g., "*.py")

    Returns:
        JSON list of matches with file, line number, and line text, or error message
    """
    # TODO: grep files only that agent has permissions on
    try:
        search_path = Path(path) if path else Path(".")
        if not search_path.exists():
            return f"Path not found: {search_path}"

        # Compile regex
        regex = re.compile(pattern)

        # Determine which files to search
        files_to_search = []
        if include:
            # Use glob to filter files by pattern
            for file_path in search_path.rglob("*"):
                if file_path.is_file() and file_path.match(include):
                    files_to_search.append(file_path)
        else:
            # Search all files recursively
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    files_to_search.append(file_path)

        matches = []
        for file_path in files_to_search:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        if regex.search(line):
                            matches.append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "text": line.rstrip("\n"),
                                }
                            )
            except (IOError, UnicodeDecodeError):
                # Skip unreadable files
                continue

        return json.dumps(matches, indent=2)
    except Exception as e:
        return f"Error grepping pattern {pattern}: {str(e)}"


# Create LangChain tool objects from the functions
write_file_tool = _create_tool(write_file)
read_file_tool = _create_tool(read_file)
read_file_lines_tool = _create_tool(read_file_lines)
create_agent_tool = _create_tool(create_agent)
delete_agent_tool = _create_tool(delete_agent)
create_task_tool = _create_tool(create_task)
close_task_tool = _create_tool(close_task)
dangerously_run_commands_tool = _create_tool(
    dangerously_run_commands,
    description="Run shell commands. WARNING: This is dangerous and should be used with caution.",
)
insert_file_lines_tool = _create_tool(insert_file_lines)
glob_files_tool = _create_tool(glob_files)
grep_files_tool = _create_tool(grep_files)


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
        "read_file_lines": read_file_lines_tool,
        "create_agent": create_agent_tool,
        "delete_agent": delete_agent_tool,
        "create_task": create_task_tool,
        "close_task": close_task_tool,
        "dangerously_run_commands": dangerously_run_commands_tool,
        "insert_file_lines": insert_file_lines_tool,
        "glob_files": glob_files_tool,
        "grep_files": grep_files_tool,
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
    "read_file_lines",
    "create_agent",
    "delete_agent",
    "create_task",
    "close_task",
    "dangerously_run_commands",
    "insert_file_lines",
    "glob_files",
    "grep_files",
    "write_file_tool",
    "read_file_tool",
    "read_file_lines_tool",
    "create_agent_tool",
    "delete_agent_tool",
    "create_task_tool",
    "close_task_tool",
    "dangerously_run_commands_tool",
    "insert_file_lines_tool",
    "glob_files_tool",
    "grep_files_tool",
    "get_all_tools",
    "get_tools_by_names",
]
