from langchain.chat_models import init_chat_model

from pathlib import Path
from dotenv import load_dotenv
from src.orchestration.tools import _create_tool
from src.orchestration.agent import BaseAgent
from src.orchestration.heartbeat import Heartbeat

import os
import yaml
import asyncio

load_dotenv()


# this should parse a sublimate-compose.yml
class BaseComposer:
    """
    So a composer should organise the agents,
    What I want it to be able to do is read a configuration file, and then it'll just run

    The name i've dubbed for this configuration file is sublimate-compose.yml

    So it'll manage agents... And stuff.

    If you want a projects agents to do something differently, you'll have to stop and start this.
    But it's on heartbeats anyway so no problems.

    Server doesn't need to interact with this directly, just can manage the config files for the agents and composer.
    """

    def __init__(self, agent_home, tools: dict, root_folder=""):
        self.agent_home = (
            isinstance(agent_home, Path) and agent_home or Path(agent_home)
        )

        self.root_folder = (
            root_folder
            and (isinstance(root_folder, Path) and root_folder or Path(root_folder))
            or self.agent_home / ".."
        ).resolve()

        self.agents = {}
        self.models = {}

        self.tools = tools
        filepath = self.agent_home / "sublimate-compose.yml"
        if os.path.exists(filepath):
            with open(filepath) as f:
                self.data = yaml.safe_load(f)
        else:
            raise FileNotFoundError(
                f"{filepath} not found! You need a sublimate-compose.yml if you want to use compose."
            )

        # check it's formatted correctly - needs
        # models
        # agents
        # heartbeats OR pipeline...
        if not all(
            [
                "models" in self.data.keys(),
                "agents" in self.data.keys(),
                "heartbeats" in self.data.keys() or "pipeline" in self.data.keys(),
            ]
        ):
            raise KeyError(
                "You need to have: models, agents and either heartbeats OR a pipeline to run compose."
            )

    def fetch_api_key_for_provider(self, provider: str) -> str:
        # TODO:
        # might have to get this from db not sure...
        # can run tests with mock i guess.
        # TEMPORARY:
        return os.environ.get("TEST_API_TOKEN")

    def get_agent(self, name):
        return self.agents.get(name, None)

    def init_chat_model(self, model, model_data):
        self.models[model] = init_chat_model(
            **model_data,
            api_key=self.fetch_api_key_for_provider(
                model_data.get(
                    "model_provider",
                    model_data.get("model", ":").split(":")[0],
                )
            ),
        )

    def init_chat_models(self):
        for model in self.data.get("models").keys():
            self.init_chat_model(model, self.data.get("models").get(model))

    def _wrap_tool_for_agent(self, tool, agent_obj):
        """
        Wrap a tool with permission checks for the given agent.
        Returns a new tool object that checks file access before delegating.
        """
        # If tool is a LangChain tool, we need to wrap its run method.
        # For simplicity, we only wrap file-related tools by name.
        # Determine if tool is file-related by checking its name.
        tool_name = None
        if hasattr(tool, "name"):
            tool_name = tool.name
        elif callable(tool) and hasattr(tool, "__name__"):
            tool_name = tool.__name__

        if tool_name in ("read_file", "write_file"):
            # Create a wrapper function that calls agent_obj.check_file_access
            if tool_name == "read_file":

                def wrapped_read_file(file_path: str) -> str:
                    if not agent_obj.check_file_access(file_path, mode="read"):
                        return f"Access denied to read file: {file_path}"
                    # Call original tool
                    if hasattr(tool, "run"):
                        return tool.run(file_path)
                    else:
                        return tool(file_path)

                # Create new tool with same signature
                if _create_tool is not None:
                    return _create_tool(
                        wrapped_read_file,
                        name="read_file",
                        description="Read a file with permission checks",
                    )
                else:
                    return wrapped_read_file
            elif tool_name == "write_file":

                def wrapped_write_file(
                    file_path: str, content: str, append: bool = False
                ) -> str:
                    if not agent_obj.check_file_access(file_path, mode="write"):
                        return f"Access denied to write file: {file_path}"
                    if hasattr(tool, "run"):
                        return tool.run(file_path, content, append)
                    else:
                        return tool(file_path, content, append)

                if _create_tool is not None:
                    return _create_tool(
                        wrapped_write_file,
                        name="write_file",
                        description="Write to a file with permission checks",
                    )
                else:
                    return wrapped_write_file
        # For other tools, return as-is
        return tool

    def init_agent(self, agent, agent_data, Agent=BaseAgent):
        # TODO: add support for param to set different:
        # heartbeat path (currently read from agent_home/heartbeats/name.md)
        # agent path (currently read from agent_home/name.md)
        # state? path (currently only read from agent_home/states/dependency_name.md) [Low importance]

        # Extract file access patterns
        file_access = agent_data.get("file_access", [])
        read_only_file_access = agent_data.get(
            "read_only_file_access", agent_data.get("read_file_access", [])
        )
        deny_file_access = agent_data.get("deny_file_access", [])

        # Create permission checker closure
        root_folder = self.root_folder

        def check_file_access(file_path, mode="read"):
            """Check file access using the agent's patterns."""
            from pathlib import Path

            path = Path(file_path)
            if path.is_absolute():
                try:
                    relative = path.relative_to(root_folder)
                except ValueError:
                    return False
            else:
                relative = path

            rel_str = str(relative).replace("\\", "/")
            if rel_str.startswith("./"):
                rel_str = rel_str[2:]

            # Helper to match pattern with directory awareness
            def match(patt, path_str):
                import fnmatch

                # Normalize slashes
                path_str = path_str.replace("\\", "/")
                patt = patt.replace("\\", "/")

                # Split into components
                path_parts = path_str.split("/")
                pattern_parts = patt.split("/")

                # Handle leading . component
                if pattern_parts and pattern_parts[0] == ".":
                    pattern_parts = pattern_parts[1:]
                if path_parts and path_parts[0] == ".":
                    path_parts = path_parts[1:]

                # Greedy matching with **
                i = j = 0
                while i < len(pattern_parts) and j < len(path_parts):
                    if pattern_parts[i] == "**":
                        i += 1
                        if i == len(pattern_parts):
                            return True
                        for k in range(j, len(path_parts) + 1):
                            if match(
                                "/".join(pattern_parts[i:]), "/".join(path_parts[k:])
                            ):
                                return True
                        return False
                    if not fnmatch.fnmatch(path_parts[j], pattern_parts[i]):
                        return False
                    i += 1
                    j += 1

                while i < len(pattern_parts) and pattern_parts[i] == "**":
                    i += 1
                return i == len(pattern_parts) and j == len(path_parts)

            # Deny first
            for pattern in deny_file_access:
                pat = pattern.replace("\\", "/")
                if pat.startswith("./"):
                    pat = pat[2:]
                if match(pat, rel_str):
                    return False

            # Read-only
            for pattern in read_only_file_access:
                pat = pattern.replace("\\", "/")
                if pat.startswith("./"):
                    pat = pat[2:]
                if match(pat, rel_str):
                    return mode == "read"

            # General file access
            for pattern in file_access:
                pat = pattern.replace("\\", "/")
                if pat.startswith("./"):
                    pat = pat[2:]
                if match(pat, rel_str):
                    return True

            return False

        # Wrap tools that need permission checks
        wrapped_tools = []
        for tool_name in agent_data.get("tools", []):
            tool = self.tools.get(tool_name)
            if not tool:
                continue
            # Wrap file-related tools
            if tool_name in ("read_file", "write_file"):
                if tool_name == "read_file":

                    def wrapped_read_file(file_path: str) -> str:
                        if not check_file_access(file_path, mode="read"):
                            return f"Access denied to read file: {file_path}"
                        if hasattr(tool, "run"):
                            return tool.run(file_path)
                        else:
                            return tool(file_path)

                    # Copy docstring/description from original tool
                    if (
                        hasattr(tool, "description")
                        and tool.description
                        and tool.description.strip()
                    ):
                        desc = tool.description.strip()
                    elif hasattr(tool, "__doc__") and tool.__doc__:
                        # Take first non-empty line of docstring
                        doc_lines = [
                            line.strip()
                            for line in tool.__doc__.split("\n")
                            if line.strip()
                        ]
                        if doc_lines:
                            desc = doc_lines[0]
                        else:
                            desc = "Read a file with permission checks"
                    else:
                        desc = "Read a file with permission checks"
                    wrapped_read_file.__doc__ = desc

                    # Create new tool object
                    if _create_tool is not None:
                        wrapped_tools.append(
                            _create_tool(
                                wrapped_read_file,
                                name="read_file",
                                description=desc,
                            )
                        )
                    else:
                        wrapped_tools.append(wrapped_read_file)
                elif tool_name == "write_file":

                    def wrapped_write_file(
                        file_path: str, content: str, append: bool = False
                    ) -> str:
                        if not check_file_access(file_path, mode="write"):
                            return f"Access denied to write file: {file_path}"
                        if hasattr(tool, "run"):
                            return tool.run(file_path, content, append)
                        else:
                            return tool(file_path, content, append)

                    # Copy docstring/description from original tool
                    if (
                        hasattr(tool, "description")
                        and tool.description
                        and tool.description.strip()
                    ):
                        desc = tool.description.strip()
                    elif hasattr(tool, "__doc__") and tool.__doc__:
                        # Take first non-empty line of docstring
                        doc_lines = [
                            line.strip()
                            for line in tool.__doc__.split("\n")
                            if line.strip()
                        ]
                        if doc_lines:
                            desc = doc_lines[0]
                        else:
                            desc = "Write to a file with permission checks"
                    else:
                        desc = "Write to a file with permission checks"
                    wrapped_write_file.__doc__ = desc

                    if _create_tool is not None:
                        wrapped_tools.append(
                            _create_tool(
                                wrapped_write_file,
                                name="write_file",
                                description=desc,
                            )
                        )
                    else:
                        wrapped_tools.append(wrapped_write_file)
            else:
                wrapped_tools.append(tool)

        self.agents[agent] = Agent(
            agent,
            self.agent_home,
            self.models[
                agent_data.get("model", agent_data.get("model_name", "default"))
            ],
            wrapped_tools,
            str(self.root_folder),
            file_access=file_access,
            read_only_file_access=read_only_file_access,
            deny_file_access=deny_file_access,
        )

        self.agents[agent].load_agent()

    def init_agents(self, Agent=BaseAgent):
        for agent in self.data.get("agents").keys():
            self.init_agent(agent, self.data.get("agents").get(agent), Agent)

    def init(self):  # init_all?
        self.init_chat_models()
        self.init_agents()

    def schedule_agent(self, name: str):
        agent = self.get_agent(name)
        if not agent:
            raise KeyError(
                f"'{name}' agent not defined in config, or this hasn't been initialised"
            )
        return agent.run

    # usability functions
    def get_heartbeats_from_settings(self):
        return self.data.get("heartbeats", {})

    def get_heartbeat_from_settings(self, name):
        if self.get_heartbeats_from_settings():
            return self.get_heartbeats_from_settings().get(name, {})
        else:
            return {}

    def get_pipeline_from_settings(self):
        return self.data.get("pipeline", [])

    def get_agents(self):
        return self.agents

    def get_models(self):
        return self.models

    def get_model(self, name):
        return self.models.get(name, {})

    def get_agent_names(self):
        return list(self.data.get("agents").keys())

    def up(self):
        # TODO: oh god
        pass

    def down(self):
        # TODO: ohh goddddd
        pass


class HeartbeatComposer(BaseComposer):
    """
    Much like composer, but will run the agents on a cronjob according to the config.

    The HeartbeatComposer is intended to start multiple cronjobs where an agent will
    be prompted to edit the codebase every X seconds/minutes/months
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heartbeats = {}

    def init_heartbeat(self, name, cron):
        self.heartbeats[name] = Heartbeat(
            cron,
            self.schedule_agent(name),
        )

    def init_heartbeats(self):
        for agent_name, hb in self.get_heartbeats_from_settings().items():
            self.init_heartbeat(
                agent_name,
                hb["schedule"],
            )

    def get_active_heartbeats(self):
        return [hb for hb in self.heartbeats.values() if hb.current]

    def get_inactive_heartbeats(self):
        return [hb for hb in self.heartbeats.values() if not hb.current]

    def get_heartbeat(self, name):
        return self.heartbeats.get(name)

    def start_heartbeat(self, name):
        heartbeat = self.get_heartbeat(name)
        if heartbeat:
            return heartbeat.start()
        return None

    def stop_heartbeat(self, name):
        heartbeat = self.get_heartbeat(name)
        if heartbeat:
            return heartbeat.stop()
        return None

    def init(self):  # init_all
        super().init()
        self.init_heartbeats()

    def up(self):
        if not self.heartbeats:
            self.init()
        for agent_name in self.get_heartbeats_from_settings().keys():
            self.start_heartbeat(agent_name)

    def down(self):
        for heartbeat in self.get_active_heartbeats().values():
            heartbeat.stop()


class PipelineComposer(BaseComposer):
    """
    Much like composer, but will run agents according to order in pipeline:list param

    PipelineComposer is intended to run the agents procedurally as specified in the config
    So basically they'll run one at a time, in the order that the pipeline list is
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proceses = {}
        self.pipeline = {}

    def init_pipeline(self):
        for segment in self.get_pipeline_from_settings():
            asyncio.gather(
                [
                    self.schedule_agent(agent_name)
                    for agent_name in self.get_agent_names()
                ]
            )
        return

    def init(self):
        super().init()
        self.init_pipeline()
        return

    def up(self):
        return

    def down(self):
        return


def create_composer(**kwargs):
    agent_home = kwargs.get("agent_home")
    if not agent_home:
        raise ValueError("No agent_home set.")

    agent_home = isinstance(agent_home, Path) and agent_home or Path(agent_home)

    filepath = agent_home / "sublimate-compose.yml"
    if os.path.exists(filepath):
        with open(filepath) as f:
            data = yaml.safe_load(f)
        if data.get("heartbeats"):
            return HeartbeatComposer(**kwargs)
        elif data.get("pipeline"):
            return PipelineComposer(**kwargs)
        else:
            return KeyError(
                "You need either a `heartbeats` or a `pipeline` in your sublimate-compose.yml if you want to create a composer!"
            )
    else:
        raise FileNotFoundError(
            f"{filepath} not found! You need a sublimate-compose.yml if you want to use compose."
        )
