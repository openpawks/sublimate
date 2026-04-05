from langchain.agents import create_agent

from datetime import datetime
from pathlib import Path

import os
import glob
import json


# base agent
class BaseAgent:
    """
    So an agent should interact with the codebase directly.
    It'll write code, and use tools that may run tests or manage other agents
    Ideally never given access to a terminal directly, but some people will do that
    anyway
    Or if it's in a docker container I guess its fine, so we'll still add that tool.

    This'll want... a few files.
    agents/agent_name.md
    agents/heartbeats/agent_name.md

    OPTIONALLY
    agents/states/depencency_name.md # for each dependency
    project-root/README.md
    project-root/AGENTS.md

    It should assign its self to tasks... not sure how this'll work yet.

    Try to complete open tasks.

    Not sure if we can have versioning and stuff that seems difficult (for a 2 man team)
    """

    def __init__(
        self,
        name: str,
        agent_home,
        model,
        tools=[],
        root_folder="",
        file_access=None,
        read_only_file_access=None,
        deny_file_access=None,
    ):
        self.name = name
        self.prompt = ""
        self.heartbeat = ""
        self.model = model
        self.context = []
        self.agent_home = (
            isinstance(agent_home, Path) and agent_home or Path(agent_home)
        )
        if not os.path.exists(self.agent_home):
            raise FileNotFoundError(
                f"{self.agent_home} not found, cwd is {os.getcwd()}"
            )
        self.root_folder = (
            root_folder
            and (isinstance(root_folder, Path) and root_folder or Path(root_folder))
            or self.agent_home / ".."
        ).resolve()
        self.file_access = file_access if file_access is not None else []
        self.read_only_file_access = (
            read_only_file_access if read_only_file_access is not None else []
        )
        self.deny_file_access = deny_file_access if deny_file_access is not None else []
        self.agent_file_paths = [
            ("prompt", self.agent_home / f"{self.name}.md"),
            ("heartbeat", self.agent_home / "heartbeats" / f"{self.name}.md"),
        ]
        self.dependencies = set({})
        self.get_chat_history = lambda x: []

        self.agent = create_agent(model=self.model, tools=tools)

    def add_dependency(self, agent):
        return self.dependencies.add(agent)

    def check_file_access(self, file_path, mode="read"):
        """
        Check if the agent is allowed to access the given file path.

        Args:
            file_path: Path to the file (can be absolute or relative to root_folder)
            mode: "read" or "write"

        Returns:
            True if allowed, False otherwise.
        """

        # Convert to Path object
        path = Path(file_path)

        # If path is absolute, make it relative to root_folder
        if path.is_absolute():
            try:
                # Compute relative path from root_folder to absolute path
                # If path is not under root_folder, deny access
                relative = path.relative_to(self.root_folder)
            except ValueError:
                # Path is outside root_folder, deny access

                return False
        else:
            relative = path

        # Normalize to string with forward slashes, remove leading ./
        rel_str = str(relative).replace("\\", "/")
        if rel_str.startswith("./"):
            rel_str = rel_str[2:]

        # Check deny patterns first
        for pattern in self.deny_file_access:
            # Normalize pattern
            pat = pattern.replace("\\", "/")
            if pat.startswith("./"):
                pat = pat[2:]
            if self._match_pattern(rel_str, pat):
                return False

        # Check read-only patterns
        for pattern in self.read_only_file_access:
            pat = pattern.replace("\\", "/")
            if pat.startswith("./"):
                pat = pat[2:]
            if self._match_pattern(rel_str, pat):
                # If matched, allow read only; deny write
                return mode == "read"

        # Check general file_access patterns
        for pattern in self.file_access:
            pat = pattern.replace("\\", "/")
            if pat.startswith("./"):
                pat = pat[2:]
            if self._match_pattern(rel_str, pat):
                return True

        # If no patterns match, deny access

        return False

    def _match_pattern(self, path_str, pattern):
        """
        Match a path string against a glob pattern respecting directory boundaries.
        Supports * (any characters except /), ? (single character except /), and **
        (zero or more directories).
        """
        import fnmatch

        # Normalize slashes
        path_str = path_str.replace("\\", "/")
        pattern = pattern.replace("\\", "/")

        # Split into components
        path_parts = path_str.split("/")
        pattern_parts = pattern.split("/")

        # Handle leading ./ or . component
        if pattern_parts and pattern_parts[0] == ".":
            pattern_parts = pattern_parts[1:]
        if path_parts and path_parts[0] == ".":
            path_parts = path_parts[1:]

        # Greedy matching with **
        i = j = 0
        while i < len(pattern_parts) and j < len(path_parts):
            if pattern_parts[i] == "**":
                # ** can match zero or more remaining directories
                # Try match remaining pattern parts against remaining path parts
                # Skip **
                i += 1
                if i == len(pattern_parts):
                    # ** at end matches everything
                    return True
                # Try match remaining pattern against each possible suffix of path
                for k in range(j, len(path_parts) + 1):
                    if self._match_pattern(
                        "/".join(path_parts[k:]), "/".join(pattern_parts[i:])
                    ):
                        return True
                return False
            if not fnmatch.fnmatch(path_parts[j], pattern_parts[i]):
                return False
            i += 1
            j += 1

        # If we have remaining pattern parts that are not **, or remaining path parts,
        # no match
        while i < len(pattern_parts) and pattern_parts[i] == "**":
            i += 1
        return i == len(pattern_parts) and j == len(path_parts)

    def load_file(self, field, filepath):  # intent to set heartbeat, prompt & context
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                setattr(self, field, f.read())
            return
        raise FileNotFoundError(filepath)

    def load_files(self, files_to_load):
        for field, filepath in files_to_load:
            try:
                self.load_file(field, filepath)
            except FileNotFoundError:
                setattr(self, field, "")

    def load_file_for(
        self, context, filepath
    ):  # intent to set heartbeat, prompt & context
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                context.append((filepath, f.read()))
        return context

    def load_files_for(self, context, filepaths):  # we _could_ load async...
        for filepath in filepaths:
            self.load_file_for(context, filepath)
        return context

    def load_agent(self):
        # TODO: compatibility with similar filepaths, heartbeats/{self.name}.md
        self.load_files(self.agent_file_paths)

        # TODO: compatibility with similar filenames like agent.md, AGENT.md, agents.md etc.
        self.load_files_for(
            self.context,
            (
                self.root_folder / "AGENTS.md",
                self.root_folder / "README.md",
                *glob.glob(
                    str(self.root_folder / ".." / "docs" / "*.*"), recursive=True
                ),
            ),
        )

    def get_task_context_as_messages(self):
        # TODO: have to write this. Anyone can write this.
        return []

    def format_message_history(
        self,
        message_history: list,
        include_prompt=True,
        include_heartbeat=True,
        include_context_files=True,
        include_dependencies=True,
    ):
        prompt_prefixes = [
            include_prompt and self.prompt,
            include_heartbeat and self.heartbeat,
            include_context_files
            and "\n".join(
                [
                    f"{filepath}\n```{file_content}```"
                    for filepath, file_content in self.context
                ]
            ),
            include_dependencies
            and "\n".join(
                [
                    f"{filepath}\n```{file_content}```"
                    for filepath, file_content in self.load_files_for(
                        [],
                        [
                            item
                            for sublist in [
                                glob.glob(
                                    str(
                                        self.agent_home
                                        / "states"
                                        / f"{dependency.name}_*.md"  # TODO:: order by earliest to latest.
                                    )
                                )
                                for dependency in self.dependencies
                            ]
                            for item in sublist
                        ],
                    )
                ]
            ),
        ]

        return {
            "messages": [
                *[{"role": "system", "content": x} for x in prompt_prefixes if x],
                *message_history,
            ]
        }

    def invoke(
        self, message_history: list, **kwargs
    ):  # maybe wait for dependencies? how? idk...
        return self.agent.invoke(self.format_message_history(message_history, **kwargs))  # type: ignore

    def ainvoke(self, message_history: list, **kwargs):
        return self.agent.ainvoke(
            self.format_message_history(message_history, **kwargs)  # type: ignore
        )

    async def run(self, **kwargs):
        """
        Run an agent and save its output to a state file.

        Args:
            name: Name of the agent to run
            message_history: Optional list of messages to provide as context
            **kwargs: Additional arguments passed to agent.invoke

        Returns:
            Agent output
        """
        # WARNING: THIS DOES NOT WAIT FOR self.dependencies to run, this should be implemented
        # so that agents don't overwrite eachother's code!
        # WARNING: MANY AGENTS WITH file write permissions may overwrite eachothers files
        # if they work simultaneously - we should add (multi-user) versioning control to stop this!
        # TODO: WAIT FOR DEPENDENCIES TO RUN

        message_history = self.get_task_context_as_messages()

        if message_history is None:
            message_history = []

        output = await self.ainvoke(message_history, **kwargs)

        # Save output to agent/states/agent_name.md
        states_dir = self.agent_home / "states"
        states_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = states_dir / f"{self.name}_{timestamp}.md"

        # Convert output to string if not already
        if isinstance(output, dict):
            output_str = json.dumps(output, indent=2, default=str)
        else:
            output_str = str(output)

        with open(state_file, "w", encoding="utf-8") as f:
            f.write(f"# Agent Run: {self.name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Message history length: {len(message_history)}\n")
            f.write("\n## Output\n")
            f.write("```\n")
            f.write(output_str)
            f.write("\n```\n")

        return output
