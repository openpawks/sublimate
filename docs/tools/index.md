# Agent Tools Reference

## Overview

This document describes the tools available to Sublimate agents. Tools are functions that agents can call to interact with the filesystem, manage tasks, and perform other operations. Each tool is implemented as a LangChain tool and can be used via the agent system.

## File System Tools

### write_file

Write content to a file.

**Signature:** `write_file(file_path: str, content: str, append: bool = False) -> str`

**Parameters:**
- `file_path`: Path to the file to write (absolute or relative)
- `content`: Content to write to the file
- `append`: If `True`, append to the file instead of overwriting (default `False`)

**Returns:**
- Success message: `"Successfully wrote to <file_path>"`
- Error message: `"Error writing to <file_path>: <error>"`

**Example:**
```python
write_file("/tmp/test.txt", "Hello, World!")
```

### read_file

Read content from a file.

**Signature:** `read_file(file_path: str) -> str`

**Parameters:**
- `file_path`: Path to the file to read

**Returns:**
- File content as string if successful
- Error message: `"File not found: <file_path>"` or `"Error reading <file_path>: <error>"`

**Example:**
```python
content = read_file("/tmp/test.txt")
```

### read_file_lines

Read specific lines from a file.

**Signature:** `read_file_lines(file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> str`

**Parameters:**
- `file_path`: Path to the file to read
- `start_line`: First line to read (1‑indexed, inclusive)
- `end_line`: Last line to read (1‑indexed, inclusive). If `None`, reads to end of file.

**Returns:**
- Requested lines as a string, or error message
- Error message: `"File not found: <file_path>"`, `"Start line <start_line> exceeds file length (<total_lines> lines)"`, or `"Error reading lines from <file_path>: <error>"`

**Example:**
```python
lines = read_file_lines("/tmp/test.txt", 2, 4)  # lines 2, 3, 4
```

### insert_file_lines

Insert content at a specific line number in a file.

**Signature:** `insert_file_lines(file_path: str, content: str, line_number: int) -> str`

**Parameters:**
- `file_path`: Path to the file
- `content`: Content to insert
- `line_number`: Line number to insert before (1‑indexed). If `line_number` exceeds total lines, content is appended.

**Returns:**
- Success message: `"Successfully inserted content at line <line_number> in <file_path>"`
- Error message: `"File not found: <file_path>"` or `"Error inserting content in <file_path>: <error>"`

**Example:**
```python
insert_file_lines("/tmp/test.txt", "new line\n", 2)
```

### glob_files

Find files matching a glob pattern.

**Signature:** `glob_files(pattern: str, path: Optional[str] = None) -> str`

**Parameters:**
- `pattern`: Glob pattern to match (supports `*`, `?`, `**` for recursion)
- `path`: Optional directory to search in (defaults to current working directory)

**Returns:**
- JSON array of absolute file paths that match the pattern
- Error message: `"Error globbing pattern <pattern>: <error>"`

**Example:**
```python
matches = glob_files("**/*.txt", "/home/project")
```

### grep_files

Search for a regex pattern in files.

**Signature:** `grep_files(pattern: str, path: Optional[str] = None, include: Optional[str] = None) -> str`

**Parameters:**
- `pattern`: Regular expression pattern to search for
- `path`: Optional directory to search in (defaults to current working directory)
- `include`: Optional file pattern to include (e.g., `"*.py"`). If not provided, all files are searched.

**Returns:**
- JSON array of matches, each with `file` (absolute path), `line` (line number), and `text` (line content)
- Error message: `"Error grepping pattern <pattern>: <error>"`

**Example:**
```python
matches = grep_files("def.*test", "/src", include="*.py")
```

## Agent Management Tools

### create_agent

Create a new agent configuration.

**Signature:** `create_agent(name: str, agent_type: str = "coder", model: str = "default", description: str = "", tools: Optional[list] = None) -> str`

**Parameters:**
- `name`: Name of the agent
- `agent_type`: Type of agent (`coder`, `tester`, `reviewer`, etc.)
- `model`: Model to use for the agent
- `description`: Description of the agent's role
- `tools`: List of tools the agent can use (defaults to `["read_file", "write_file"]`)

**Returns:**
- Success message with the generated configuration in JSON format
- Error message: `"Error creating agent: <error>"`

**Example:**
```python
create_agent("test_agent", "coder", "gpt-4", "An agent for testing")
```

### delete_agent

Delete an agent configuration.

**Signature:** `delete_agent(name: str) -> str`

**Parameters:**
- `name`: Name of the agent to delete

**Returns:**
- Success message: `"Agent '<name>' marked for deletion. (Note: This is a mock implementation)"`
- Error message: `"Error deleting agent: <error>"`

**Example:**
```python
delete_agent("test_agent")
```

## Task Management Tools

### create_task

Create a new task for agents to work on.

**Signature:** `create_task(title: str, description: str, agent: Optional[str] = None, priority: str = "medium", tags: Optional[list] = None) -> str`

**Parameters:**
- `title`: Title of the task
- `description`: Detailed description of the task
- `agent`: Optional agent to assign the task to
- `priority`: Priority level (`low`, `medium`, `high`, `critical`)
- `tags`: Optional list of tags for the task

**Returns:**
- Task ID and task data in JSON format
- Error message: `"Error creating task: <error>"`

**Example:**
```python
create_task("Fix bug", "There is a bug in the login flow", "coder", "high", ["bug", "login"])
```

### close_task

Close a task, marking it as complete.

**Signature:** `close_task(task_id: str, notes: str = "") -> str`

**Parameters:**
- `task_id`: ID of the task to close
- `notes`: Optional notes about the completion

**Returns:**
- Success message: `"Task <task_id> closed. Notes: <notes>"`
- Error message: `"Error closing task: <error>"`

**Example:**
```python
close_task("task_20250101_123456", "Fixed the issue")
```

## System Tools

### dangerously_run_commands

Run shell commands. **WARNING:** This is dangerous and should be used with extreme caution.

**Signature:** `dangerously_run_commands(command: str, timeout: int = 30) -> str`

**Parameters:**
- `command`: Shell command to execute
- `timeout`: Timeout in seconds (default 30)

**Returns:**
- JSON object with `returncode`, `stdout`, `stderr`, and `command`
- Error message if command times out or fails

**Example:**
```python
dangerously_run_commands("ls -la", timeout=10)
```

## Utility Functions

### get_all_tools

Get a dictionary of all available tools as LangChain tool objects.

**Signature:** `get_all_tools() -> Dict[str, Any]`

**Returns:**
- Dictionary mapping tool names to LangChain tool objects

### get_tools_by_names

Get a dictionary of tools filtered by names.

**Signature:** `get_tools_by_names(tool_names: list) -> Dict[str, Any]`

**Parameters:**
- `tool_names`: List of tool names to include

**Returns:**
- Dictionary mapping tool names to tool objects (only those that exist)

## Usage Example

```python
from src.orchestration.tools import get_all_tools

tools = get_all_tools()
write_file_tool = tools["write_file"]
result = write_file_tool.run({"file_path": "/tmp/test.txt", "content": "Hello"})
```
