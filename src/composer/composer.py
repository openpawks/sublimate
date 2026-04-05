from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

from croniter import croniter
from datetime import datetime

from pathlib import Path
import os, glob, yaml, asyncio, json


# base task, handles for issues
class BaseTask:
    def __init__(self):
        return


# base agent
class BaseAgent:
    """
    So an agent should interact with the codebase directly.
    It'll write code, and use tools that may run tests or manage other agents
    Ideally never given access to a terminal directly, but some people will do that anyway
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
        )
        self.agent_file_paths = [
            ("prompt", self.agent_home / f"{self.name}.md"),
            ("heartbeat", self.agent_home / "heartbeats" / f"{self.name}.md"),
        ]
        self.dependencies = set({})
        self.get_chat_history = lambda x: []

        self.agent = create_agent(model=self.model, tools=tools)

    def add_dependency(self, agent):
        return self.dependencies.add(agent)

    def load_file(self, field, filepath):  # intent to set heartbeat, prompt & context
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                setattr(self, field, f.read())
            return
        raise FileNotFoundError(filepath)

    def load_files(self, files_to_load):
        for field, filepath in files_to_load:
            self.load_file(field, filepath)

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
                *glob.glob(str(self.root_folder / ".." / "docs" / "*"), recursive=True),
            ),
        )

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
                                        / f"{dependency.name}.md"
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
        )

        self.agents = {}
        self.models = {}

        # TODO: find out how we will add tools to this... (theyre just a dict[str:function])
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
        return "dummy-api-key"

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

    def init_agent(self, agent, agent_data, Agent=BaseAgent):
        # TODO: add support for param to set different:
        # heartbeat path (currently read from agent_home/heartbeats/name.md)
        # agent path (currently read from agent_home/name.md)
        # state? path (currently only read from agent_home/states/dependency_name.md) [Low importance]

        self.agents[agent] = Agent(
            agent,
            self.agent_home,
            self.models[
                agent_data.get("model", agent_data.get("model_name", "default"))
            ],
            [
                tool
                for tool in [
                    self.tools.get(x, None) for x in agent_data.get("tools", [])
                ]
                if tool
            ],  # probably a better way to do this but your boy's a moron
            str(self.root_folder),
        )

        self.agents[agent].load_agent()

    def init_agents(self, Agent=BaseAgent):
        for agent in self.data.get("agents").keys():
            self.init_agent(agent, self.data.get("agents").get(agent), Agent)

    def init(self):  # init_all?
        self.init_chat_models()
        self.init_agents()

    def run_agent(self, name: str, message_history: list = None, **kwargs):
        """
        Run an agent and save its output to a state file.

        Args:
            name: Name of the agent to run
            message_history: Optional list of messages to provide as context
            **kwargs: Additional arguments passed to agent.invoke

        Returns:
            Agent output
        """
        if message_history is None:
            message_history = []

        agent = self.get_agent(name)
        if not agent:
            raise ValueError(f"Agent '{name}' not found")

        output = agent.invoke(message_history, **kwargs)

        # Save output to agent/states/agent_name.md
        states_dir = self.agent_home / "states"
        states_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = states_dir / f"{name}_{timestamp}.md"

        # Convert output to string if not already
        if isinstance(output, dict):
            output_str = json.dumps(output, indent=2, default=str)
        else:
            output_str = str(output)

        with open(state_file, "w", encoding="utf-8") as f:
            f.write(f"# Agent Run: {name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Message history length: {len(message_history)}\n")
            f.write("\n## Output\n")
            f.write("```\n")
            f.write(output_str)
            f.write("\n```\n")

        return output

    # usability functions
    def get_heartbeats_from_settings(self):
        return self.data.get("heartbeats", {})

    def get_heartbeat_from_settings(self, name):
        if self.get_heartbeats_from_settings():
            return self.get_heartbeats_from_settings().get(name, {})
        else:
            return {}

    def get_pipeline(self):
        return self.data.get("pipeline", {})

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


class Heartbeat:
    def __init__(self, agent, cron):
        self.agent = agent
        self.cron = cron
        self.current = None

    def get_next(self):
        return croniter(self.cron, datetime.now())

    def wait_until_datetime(self, target_datetime):
        now = datetime.now()
        delta = (target_datetime - now).total_seconds()
        if delta > 0:
            return asyncio.sleep(delta)
        return asyncio.sleep(0)

    async def daemon(self):
        while True:
            await self.wait_until_datetime(self.get_next())
            await self.abeat()

    def get_task_context_as_messages(self):
        # TODO: have to write this. Anyone can write this.
        return []

    def beat(self):
        # TODO: invoke with task or active task etc.
        # we should probably also save task data incase program stops suddenly
        return self.agent.invoke(self.get_task_context_as_messages())

    def abeat(self):
        # invoke agent, asynchronously i guess
        return self.agent.ainvoke(self.get_task_context_as_messages())

    def start(self):
        if self.current:
            raise RuntimeError("Heartbeat already running")
        self.current = asyncio.create_task(self.daemon())
        return self.current

    def stop(self):
        if self.current:
            # stop asyncio create_task object.
            return self.current.cancel()
        return None  # no heartbeat to kill


class HeartbeatComposer(BaseComposer):
    """
    Much like composer, but will run the agents on a cronjob according to the config.
    """

    def __init__(self, agent_home, tools: dict, root_folder=""):
        super().__init__(agent_home, tools, root_folder)
        self.heartbeats = {}

    def init_heartbeat(self, name, cron):
        self.heartbeats[name] = Heartbeat(self.get_agent(name), cron)

    def init_heartbeats(self):
        for agent_name, hb in self.get_heartbeats_from_settings().items():
            self.init_heartbeat(agent_name, hb["schedule"])

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


class PipelineComposer(BaseComposer):
    """
    Much like composer, but will run agents according to order in pipeline:list param
    """

    pass
