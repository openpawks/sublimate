from src.orchestration.agent import AgentFactory

from src.schemas.data import TaskData
from src.schemas.task import TaskUpdate

from git.exc import NoSuchPathError
import git


class BaseTask:
    def __init__(
        self,
        data: TaskData,
        project=None,
        chat=None,
    ):
        """
        Creates a BaseTask object.
        The BaseTask object invokes agents until they finish their task

        Args:
            data: TaskData object with task configuration
            project: optional pre-resolved BaseProject reference
            chat: optional pre-resolved BaseChat reference
        """
        self._data = data
        self._project = project
        self._chat = chat
        self.name = self._data.name

        self.task_tools = []

        self.repeating_until_complete = False
        self.active_agent_name = ""
        self.agents = {}

        self.repo = None

    @property
    def project(self):
        if self._project is None:
            from src.services import registry

            self._project = registry.project_service.get_base_project_by_id(
                self._data.project_id
            )
        return self._project

    @project.setter
    def project(self, value):
        self._project = value

    @property
    def chat(self):
        if self._chat is None:
            from src.services import registry

            self._chat = registry.chat_service.get_base_chat_by_id(self._data.chat_id)
        return self._chat

    @chat.setter
    def chat(self, value):
        self._chat = value

    @property
    def open(self):
        return self._data.open

    def init_repo(self):
        try:
            self.repo = git.Repo(self._data.root_dir)
            assert not self.repo.bare
            return self.repo
        except (NoSuchPathError, AssertionError) as e:
            print(f"Path {self._data.root_dir} is wrong!\nERROR: {e}")

    def get_repo(self):
        if self.repo:
            return self.repo
        return self.init_repo()

    def refresh_task_tools(self):
        """
        Add task specific tools (mostly memory stuff) to each agent
        Clear current agent, so that agents will refresh with new tools
        """
        self.task_tools = [
            # self.read_todos,
            # self.edit_todos,
            self.close,
            self.commit_changes,
            self.tree,
            self.write_file,
            self.read_file,
            self.edit_file_lines,
            self.read_file_lines,
            self.shell_command,
            self.commit_changes,
            self.close,
        ]

        if len(self.agents) > 1:
            self.task_tools = [
                *self.task_tools,
                self.next_agent,
                self.set_active_agent,
                self.list_agents_as_text,
            ]

        # seems unneccessary actually, langchain will automatically map tools and such
        # self.task_tools = [_create_tool(x) for x in self.task_tools]

        for agent in self.agents.values():
            agent.tools = self.task_tools
            agent.agent = None

    def init_all(self):
        self.init_repo()
        self.refresh_task_tools()

    def init_agent(self, agent):
        """
        Langchain's create_agent function, but task specific tools
        """
        agent.init_agent(tools=[*self.task_tools, *agent.tools])

    # ========= AGENT TOOLS ==========
    def read_todos(self):
        """Read todo list"""
        return self._data.todos

    async def edit_todos(self, todos: str):
        """Write/edit todo list, rewrite the whole thing, with marks for what has already been done."""
        from src.services import registry

        updated_task = await registry.task_service.update_task(
            self._data.id, TaskUpdate(todos=todos)
        )
        if updated_task:
            self._data.todos = todos
        return updated_task

    def close_task(self):
        """Close task when you think its done. Do this when you are sure, and tests have passed."""
        self.repeating_until_complete = False
        self.close()
        return

    def next_agent(self):
        """Cycle the conversation to the next agent"""
        if not self.active_agent_name or self.active_agent_name not in self.agents:
            if self.agents:
                self.set_active_agent(list(self.agents.keys())[0])
                return "Success"
            else:
                return "No agents available"

        keys = list(self.agents.keys())
        current_index = keys.index(self.active_agent_name)
        next_index = current_index + 1
        if next_index < len(keys):
            self.set_active_agent(keys[next_index])
        else:
            self.set_active_agent(keys[0])
        return "Success"

    def set_active_agent(self, name: str):
        """Allow another worker to work on this, should use for todos where another agent is likely more suitable."""
        if name in self.agents.keys():
            self.active_agent_name = name
        else:
            return f"Agent '{name}' does not exist. The current agents assigned are\n{self.list_agents_as_text(name)}"

    def list_agents_as_text(self, name: str = ""):
        """List agents in chat."""
        return "\n".join(list(self.agents.keys()))

    def get_agent(self, name: str):
        return self.agents.get(name, None)

    def get_active_agent(self):
        """Find the name of whatever agent is active"""
        if self.active_agent_name:
            agent_name = self.active_agent_name
        elif self.agents:
            agent_name = list(self.agents.keys())[0]
        else:
            raise ValueError("No agents set!")

        return self.agents.get(agent_name)

    def _resolve_path(self, path: str) -> str:
        """
        Resolve a user-provided path relative to root_dir, preventing directory traversal.
        Returns the absolute, normalized path if it's within root_dir, otherwise raises ValueError.
        """
        import os

        root = os.path.abspath(self._data.root_dir)
        joined = os.path.normpath(os.path.join(root, path))
        if not joined.startswith(root):
            raise ValueError(
                f"Path '{path}' escapes the project root and is not allowed."
            )
        return joined

    def tree(self, path_from: str = "./") -> str:
        """
        Recursively list the directory structure starting from path_from (relative to root_dir).
        Returns a formatted string showing the tree. Prevents access outside root_dir.

        Args:
            path_from: relative directory path to start from (default: "./")

        Returns:
            A string representation of the directory tree.
        """
        import os

        target = self._resolve_path(path_from)
        if not os.path.isdir(target):
            return f"Error: '{path_from}' is not a directory or does not exist."

        lines = []
        for root, dirs, files in os.walk(target):
            rel = os.path.relpath(root, target)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            indent = "    " * depth
            lines.append(f"{indent}{os.path.basename(root) if depth > 0 else '.'}/")
            sub_indent = "    " * (depth + 1)
            for f in files:
                lines.append(f"{sub_indent}{f}")
        return "\n".join(lines)

    def write_file(self, file_path: str):
        """
        Write content to a file. The file_path is relative to root_dir.
        Prompts the user for content via stdin. Prevents access outside root_dir.

        Args:
            file_path: relative path to the file to write
        """
        import os

        target = self._resolve_path(file_path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        content = input("Enter file content (Ctrl+D to finish):\n")
        with open(target, "w") as f:
            f.write(content)

    def read_file(self, file_path: str) -> str:
        """
        Read and return the contents of a file. The file_path is relative to root_dir.
        Prevents access outside root_dir.

        Args:
            file_path: relative path to the file to read

        Returns:
            The contents of the file as a string.
        """
        # TODO: no read sensitive files
        target = self._resolve_path(file_path)
        with open(target, "r") as f:
            return f.read()

    def edit_file_lines(self, file_path: str, from_lines: int = 0, to_lines: int = 40):
        """
        Read specific line range from a file and prompt the user to rewrite those lines.
        The file_path is relative to root_dir. Prevents access outside root_dir.
        Lines are 0-indexed. After user provides replacement content, the file is updated.

        Args:
            file_path: relative path to the file
            from_lines: start line index (0-indexed, inclusive)
            to_lines: end line index (0-indexed, exclusive)
        """
        target = self._resolve_path(file_path)
        with open(target, "r") as f:
            all_lines = f.readlines()

        if from_lines < 0 or to_lines > len(all_lines) or from_lines >= to_lines:
            raise ValueError(
                f"Invalid line range: {from_lines}-{to_lines}. File has {len(all_lines)} lines."
            )

        print(f"Current lines {from_lines}-{to_lines - 1}:")
        for i in range(from_lines, to_lines):
            print(f"{i}: {all_lines[i]}", end="")

        print("\nEnter replacement content (Ctrl+D to finish):")
        replacement = []
        while True:
            try:
                line = input()
                replacement.append(line)
            except EOFError:
                break

        new_content = (
            all_lines[:from_lines]
            + [x + "\n" for x in replacement]
            + all_lines[to_lines:]
        )
        with open(target, "w") as f:
            f.writelines(new_content)

    def read_file_lines(
        self, file_path: str, from_lines: int = 0, to_lines: int = 40
    ) -> str:
        """
        Read specific lines from a file. The file_path is relative to root_dir.
        Prevents access outside root_dir. Lines are 0-indexed.

        Args:
            file_path: relative path to the file
            from_lines: start line index (0-indexed, inclusive)
            to_lines: end line index (0-indexed, exclusive)

        Returns:
            The requested lines joined as a string.
        """
        target = self._resolve_path(file_path)
        with open(target, "r") as f:
            all_lines = f.readlines()

        if from_lines < 0 or to_lines > len(all_lines) or from_lines >= to_lines:
            raise ValueError(
                f"Invalid line range: {from_lines}-{to_lines}. File has {len(all_lines)} lines."
            )

        return "".join(all_lines[from_lines:to_lines])

    def shell_command(self, command: str) -> str:
        """
        Execute a shell command within the project root directory.
        The command runs with root_dir as the working directory to limit impact.
        Validates the command to prevent operations that escape the project root.

        Args:
            command: the shell command to execute

        Returns:
            The stdout and stderr output of the command as a string.
        """
        import os
        import re
        import subprocess

        root = os.path.abspath(self._data.root_dir)

        blocklist = [
            ";",
            "&&",
            "||",
            "|",
            "`",
            "$(",  # chaining
            "..",
            "~",  # path traversal
        ]
        for token in blocklist:
            if token in command:
                raise ValueError(
                    f"Command contains disallowed token '{token}': {command}"
                )

        redirect_out_pattern = re.compile(r"(?:^|\s)>(?:>)?\s*\S+")
        if redirect_out_pattern.search(command):
            raise ValueError(
                f"Command contains output redirection which may escape root: {command}"
            )

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=root,
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        return output

    # END OF AGENT TOOLS
    def resign_agent(self, agent_name: str):
        """Remove the agent from the task"""
        if self.get_agent(agent_name):
            del self.agents[agent_name]
            return 1
        else:
            raise KeyError(f"{agent_name} not found")

    def resign_agents(self, agent_names: list):
        """Remove multiple agents from the task"""
        for agent_name in agent_names:
            self.resign_agent(agent_name)

    def assign_agent(self, agent_factory: AgentFactory):
        """
        Assign an agent to this task, using an agent factory
        The agent_factory creates a clone of the agent, with all the configuration
        derived from the parent
        """
        if self.get_agent(agent_factory.name):
            print(f"{agent_factory.name} already assigned")
            return None
        new_agent = agent_factory.create_worker(self._data.root_dir)
        new_agent.task = self
        self.agents[new_agent.name] = new_agent

    def assign_agents(self, agents: list[AgentFactory]):
        """
        Assign multiple agents to this task,
        saves you writing a for loop yourself.
        """
        for agent in agents:
            self.assign_agent(agent)

    def invoke_agent_from_name(self, name, *args, **kwargs):
        """
        Invoke an agent by name
        """
        agent = self.get_agent(name)
        return self.invoke_agent(agent, *args, **kwargs)

    def invoke_agent(self, agent, messages: list[dict] = []):
        """
        Invoke an agent with the task's chat history.
        You should use this as opposed to directly
        agent.ainvoke, because this will check if there's no
        current agent, to avoid initialising all agents
        if many agents are assigned to a task

        Args:
            messages: optional extra messages if you want to prompt inject (not saved)
        """
        if not agent.agent:
            self.init_agent(agent)
        return agent.ainvoke([*self.chat.get_messages(), *messages])

    def get_messages(self, *args, **kwargs):
        """
        Get the task's chat history
        """
        return self.chat.get_messages(*args, **kwargs)

    def was_created_at(self):
        return self.chat.was_created_at()

    def was_last_updated_at(self):
        return self.chat.was_last_updated_at()

    def commit_changes(self, message: str):
        """
        Add everything to staging area, and commit changes.

        Args:
            message: commit message
        """
        repo = self.get_repo()
        repo.index.add("*")
        return repo.index.commit(message)

    async def close(self):
        self.repeating_until_complete = False
        await self.project.close_task(self._data.id, self._data.name)

    async def repeat_until_complete(self, db, max_iterations: int = 100):
        """
        Repeat this task, until the agent requests to stop

        Args:
            db: database session
            max_iterations: How many messages until it stops automatically
        """
        if not self.repo:
            self.init_all()

        self.repeating_until_complete = True
        iteration = 0

        while (
            self.repeating_until_complete and self.open and iteration < max_iterations
        ):
            # TODO:
            # - stream this agent.invoke
            # - on task initation, run tree automatically and add that as message,
            #   - must check if not already been sent,
            #   - or if detects changes not managed by task, resend new
            # NOTE:
            # after a more comprehensive understanding of how this works, maybe
            # this while true loop is more unneccessary than i thought,
            # maybe it should be a for loop for assigned agents?
            agent = self.get_active_agent()
            output = await self.invoke_agent(self.agent, self.chat.get_messages())

            await self.chat.add_message(
                db=db,
                role="assistant",
                content=output.content,
                username=agent.name,
            )
            iteration += 1

            if iteration >= max_iterations:
                self.repeating_until_complete = False
                await self.chat.add_message(
                    db=db,
                    role="system",
                    content=f"Stopped after {max_iterations} iterations (safety limit).",
                    username="system",
                )
            if self.repo and self.open:
                try:
                    self.commit_changes("Auto commit on task completion")
                except Exception as e:
                    print(f"Auto commit failed: {e}")
        return
