from langchain.agents import create_agent
from langchain.agents.middleware import (
    ToolRetryMiddleware,
    TodoListMiddleware,
    ModelRetryMiddleware,
    FilesystemFileSearchMiddleware,
)
from langchain.chat_models import init_chat_model

from src.schemas.data import AgentData
from src.services import registry

from pathlib import Path
import yaml


class WorkerAgent:
    def __init__(
        self,
        model,
        root_dir,
        chat_id: int = -1,
        name: str = "",
        prompt: str = "",
        heartbeat_prompt: str = "",
    ):
        """
        An agent that tasks will call upon. This agent will write files and run commands and such

        Args:
            model: langchain chat model
            prompt: initial prompt
            heartbeat_prompt: prompt to be called every now and again, for agent to work autonomously
            name: agent nickname
        """
        self.model = model
        self.name = name
        self.prompt = prompt
        self.tools = []
        self.heartbeat_prompt = heartbeat_prompt
        self.root_dir = root_dir

        self.agent = None

    def init_agent(self, **kwargs):
        """
        Create the agent object, with tools and such
        """
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            middleware=[
                TodoListMiddleware(),
                ToolRetryMiddleware(
                    max_retries=3,
                    backoff_factor=2.0,
                    initial_delay=1.0,
                ),
                ModelRetryMiddleware(
                    max_retries=3,
                    backoff_factor=2.0,
                    initial_delay=1.0,
                ),
                FilesystemFileSearchMiddleware(
                    root_path=self.root_dir,
                    use_ripgrep=True,
                ),
            ],
            system_prompt=self.prompt,
            checkpointer=registry.checkpointer**kwargs,
        )
        return self.agent

    def ainvoke(self, messages: list, *args, **kwargs):
        """
        Invoke the agent to start working.

        Args:
            messages: previous messages
        """
        return self.agent.ainvoke(
            {"messages": [{"role": "system", "content": self.prompt}, *messages]}
        )


class ChatAgent:
    """
    This will be an agent that you can chat to in a chat window,
    and it'll be able to create tasks, close tasks, etc.
    send messages to tasks.

    Maybe this is redundant
    """

    pass


class AgentFactory:
    def __init__(
        self,
        data: AgentData,
        **kwargs,
    ):
        """
        Create an agent factory
        This'll have the configuration for the agent, which then a Task will actually create the agent, to do things
        So set your config for the agent here.

        Args:
            data: AgentData object with configuration (name, provider, model, prompts, settings)
        """
        self._data = data

        self.name = self._data.name
        self.provider_name = self._data.provider_id
        self.model_name = self._data.model_name
        self.prompt = self._data.prompt
        self.heartbeat_prompt = self._data.heartbeat_prompt

        try:
            self.kwargs = yaml.safe_load(self._data.settings_yaml or "") or {}
        except yaml.YAMLError:
            self.kwargs = {}

        self.model = None

    def init_chat_model(self):
        self.model = init_chat_model(
            provider=self.provider_name,
            model=self.model_name,
            **self.kwargs.get("model", {}),
        )

    def create_worker(self, root_dir: Path | str):
        """
        Create a WorkerAgent object, using some configuration settings
        from this AgentFactory
        """
        if not self.model:
            self.init_chat_model()

        return WorkerAgent(
            model=self.model,
            root_dir=root_dir,
            name=self.name,
            prompt=self.prompt,
            heartbeat_prompt=self.heartbeat_prompt,
        )
