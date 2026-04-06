"""
Tests for the tools module.
"""

import pytest
import tempfile
import os
import subprocess
import json
from unittest.mock import patch, MagicMock

from src.orchestration.tools import (
    write_file,
    read_file,
    create_agent,
    delete_agent,
    create_task,
    close_task,
    dangerously_run_commands,
    insert_file_lines,
    glob_files,
    grep_files,
    get_all_tools,
    get_tools_by_names,
    write_file_tool,
    read_file_tool,
    insert_file_lines_tool,
    glob_files_tool,
    grep_files_tool,
)


class TestWriteFileTool:
    """Tests for write_file tool."""

    def test_write_file_success(self):
        """Test writing to a file successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            result = write_file(file_path, "Hello, World!")

            assert "Successfully wrote to" in result
            with open(file_path, "r") as f:
                content = f.read()
            assert content == "Hello, World!"

    def test_write_file_append(self):
        """Test appending to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            # Write initial content
            write_file(file_path, "Hello")
            # Append more content
            result = write_file(file_path, ", World!", append=True)

            assert "Successfully wrote to" in result
            with open(file_path, "r") as f:
                content = f.read()
            assert content == "Hello, World!"

    def test_write_file_create_directory(self):
        """Test that directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "subdir", "test.txt")
            result = write_file(file_path, "Hello")

            assert "Successfully wrote to" in result
            assert os.path.exists(file_path)


class TestReadFileTool:
    """Tests for read_file tool."""

    def test_read_file_success(self):
        """Test reading a file successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            with open(file_path, "w") as f:
                f.write("Hello, World!")

            result = read_file(file_path)
            assert result == "Hello, World!"

    def test_read_file_not_found(self):
        """Test reading a non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nonexistent.txt")
            result = read_file(file_path)

            assert "File not found" in result


class TestCreateAgentTool:
    """Tests for create_agent tool."""

    def test_create_agent_basic(self):
        """Test creating an agent with minimal parameters."""
        result = create_agent("test-agent", "coder")

        assert "Created agent 'test-agent'" in result
        assert "coder" in result
        assert "Configuration:" in result

    def test_create_agent_with_tools(self):
        """Test creating an agent with specific tools."""
        result = create_agent("test-agent", "coder", tools=["read_file", "write_file"])

        assert "Created agent 'test-agent'" in result
        # Check that tools list appears in the result (JSON may be pretty-printed)
        assert '"read_file"' in result
        assert '"write_file"' in result
        assert '"tools"' in result


class TestDeleteAgentTool:
    """Tests for delete_agent tool."""

    def test_delete_agent(self):
        """Test deleting an agent."""
        result = delete_agent("test-agent")

        assert "marked for deletion" in result


class TestCreateTaskTool:
    """Tests for create_task tool."""

    def test_create_task_basic(self):
        """Test creating a task with minimal parameters."""
        result = create_task("Test task", "This is a test task")

        assert "Created task 'Test task'" in result
        assert "task_" in result  # Should have task ID prefix
        assert '"status"' in result and '"open"' in result

    def test_create_task_with_tags(self):
        """Test creating a task with tags."""
        result = create_task("Test task", "Description", tags=["bug", "urgent"])

        assert '"tags"' in result and '"bug"' in result and '"urgent"' in result


class TestCloseTaskTool:
    """Tests for close_task tool."""

    def test_close_task(self):
        """Test closing a task."""
        result = close_task("task_123", "Completed successfully")

        assert "Task task_123 closed" in result
        assert "Completed successfully" in result


class TestDangerouslyRunCommandsTool:
    """Tests for dangerously_run_commands tool."""

    @patch("subprocess.run")
    def test_dangerously_run_commands_success(self, mock_run):
        """Test running a command successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = dangerously_run_commands("echo Hello")

        assert '"returncode": 0' in result
        assert '"stdout": "Hello\\n"' in result

    @patch("subprocess.run")
    def test_dangerously_run_commands_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("echo Hello", 30)

        result = dangerously_run_commands("echo Hello", timeout=5)

        assert "timed out" in result


class TestToolUtilities:
    """Tests for tool utility functions."""

    def test_get_all_tools(self):
        """Test get_all_tools returns all tools."""
        tools = get_all_tools()

        expected_tools = [
            "write_file",
            "read_file",
            "create_agent",
            "delete_agent",
            "create_task",
            "close_task",
            "dangerously_run_commands",
            "insert_file_lines",
            "glob_files",
            "grep_files",
        ]

        for tool_name in expected_tools:
            assert tool_name in tools

        # Check that values are callable or have run method
        for tool_name, tool_obj in tools.items():
            if hasattr(tool_obj, "run"):
                # LangChain tool object
                assert callable(tool_obj.run)
            else:
                # Raw function or mock
                assert callable(tool_obj)

    def test_get_tools_by_names(self):
        """Test getting tools by names."""
        tool_names = ["write_file", "read_file", "create_task"]
        tools = get_tools_by_names(tool_names)

        assert set(tools.keys()) == set(tool_names)

        # Test with non-existent tool
        tools = get_tools_by_names(["write_file", "nonexistent_tool"])
        assert "write_file" in tools
        assert "nonexistent_tool" not in tools


class TestInsertFileLinesTool:
    """Tests for insert_file_lines tool."""

    def test_insert_file_lines_success(self):
        """Test inserting lines at a specific line number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            # Create initial content
            with open(file_path, "w") as f:
                f.write("line1\nline2\nline3\n")

            result = insert_file_lines(file_path, "inserted\n", 2)
            assert "Successfully inserted" in result

            with open(file_path, "r") as f:
                lines = f.readlines()
            assert lines == ["line1\n", "inserted\n", "line2\n", "line3\n"]

    def test_insert_file_lines_append(self):
        """Test inserting beyond total lines (append)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            with open(file_path, "w") as f:
                f.write("line1\n")

            result = insert_file_lines(file_path, "line2\n", 10)
            assert "Successfully inserted" in result

            with open(file_path, "r") as f:
                lines = f.readlines()
            assert lines == ["line1\n", "line2\n"]

    def test_insert_file_lines_prepend(self):
        """Test inserting at line 1 (prepend)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            with open(file_path, "w") as f:
                f.write("original\n")

            result = insert_file_lines(file_path, "new first line\n", 1)
            assert "Successfully inserted" in result

            with open(file_path, "r") as f:
                lines = f.readlines()
            assert lines == ["new first line\n", "original\n"]

    def test_insert_file_lines_file_not_found(self):
        """Test inserting into a non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nonexistent.txt")
            result = insert_file_lines(file_path, "content", 1)
            assert "File not found" in result


class TestGlobFilesTool:
    """Tests for glob_files tool."""

    def test_glob_files_success(self):
        """Test globbing with matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            open(os.path.join(tmpdir, "foo.txt"), "w").close()
            open(os.path.join(tmpdir, "bar.txt"), "w").close()
            open(os.path.join(tmpdir, "baz.py"), "w").close()

            result = glob_files("*.txt", path=tmpdir)
            matches = json.loads(result)
            # Should contain foo.txt and bar.txt (absolute paths)
            assert len(matches) == 2
            filenames = [os.path.basename(p) for p in matches]
            assert "foo.txt" in filenames
            assert "bar.txt" in filenames
            assert "baz.py" not in filenames

    def test_glob_files_no_matches(self):
        """Test globbing with no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = glob_files("*.md", path=tmpdir)
            matches = json.loads(result)
            assert matches == []

    def test_glob_files_recursive(self):
        """Test globbing with recursive pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "sub")
            os.mkdir(subdir)
            open(os.path.join(subdir, "file.txt"), "w").close()

            result = glob_files("**/*.txt", path=tmpdir)
            matches = json.loads(result)
            assert len(matches) == 1
            assert matches[0].endswith("sub/file.txt")


class TestGrepFilesTool:
    """Tests for grep_files tool."""

    def test_grep_files_success(self):
        """Test grepping with matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            with open(file_path, "w") as f:
                f.write("hello world\nfoo bar\nhello again\n")

            result = grep_files("hello", path=tmpdir)
            matches = json.loads(result)
            assert len(matches) == 2
            for match in matches:
                assert match["file"] == file_path
                assert "hello" in match["text"]

    def test_grep_files_no_matches(self):
        """Test grepping with no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            with open(file_path, "w") as f:
                f.write("hello world\n")

            result = grep_files("nonexistent", path=tmpdir)
            matches = json.loads(result)
            assert matches == []

    def test_grep_files_with_include(self):
        """Test grepping with file pattern inclusion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = os.path.join(tmpdir, "a.txt")
            py_file = os.path.join(tmpdir, "b.py")
            with open(txt_file, "w") as f:
                f.write("target\n")
            with open(py_file, "w") as f:
                f.write("target\n")

            result = grep_files("target", path=tmpdir, include="*.txt")
            matches = json.loads(result)
            assert len(matches) == 1
            assert matches[0]["file"] == txt_file

    def test_grep_files_path_not_found(self):
        """Test grepping with non-existent path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = os.path.join(tmpdir, "nonexistent")
            result = grep_files("pattern", path=nonexistent)
            assert "Path not found" in result


class TestToolObjects:
    """Tests for LangChain tool objects."""

    def test_write_file_tool_object(self):
        """Test that write_file_tool is a LangChain tool object."""
        # Check if it has run method (LangChain tool) or is callable
        if hasattr(write_file_tool, "run"):
            assert callable(write_file_tool.run)
        else:
            assert callable(write_file_tool)

    def test_read_file_tool_object(self):
        """Test that read_file_tool is a LangChain tool object."""
        if hasattr(read_file_tool, "run"):
            assert callable(read_file_tool.run)
        else:
            assert callable(read_file_tool)

    def test_insert_file_lines_tool_object(self):
        """Test that insert_file_lines_tool is a LangChain tool object."""
        if hasattr(insert_file_lines_tool, "run"):
            assert callable(insert_file_lines_tool.run)
        else:
            assert callable(insert_file_lines_tool)

    def test_glob_files_tool_object(self):
        """Test that glob_files_tool is a LangChain tool object."""
        if hasattr(glob_files_tool, "run"):
            assert callable(glob_files_tool.run)
        else:
            assert callable(glob_files_tool)

    def test_grep_files_tool_object(self):
        """Test that grep_files_tool is a LangChain tool object."""
        if hasattr(grep_files_tool, "run"):
            assert callable(grep_files_tool.run)
        else:
            assert callable(grep_files_tool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
