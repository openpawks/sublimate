from langchain.agents import create_agent
from langchain.chat_models import init_chat_model


class BaseAgent:
    def __init__(
        self,
        model,
        name: str = "",
        prompt: str = "",
        heartbeat_prompt: str = "",
    ):
        """
        An agent that tasks will call upon

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

        self.agent = None

    def init_agent(self, **kwargs):
        """
        Create the agent object, with tools and such
        """
        # TODO: add tool retry middleware by default
        # - also add tools, unsure how current tools will integrate with this
        self.agent = create_agent(model=self.model, system_prompt=self.prompt, **kwargs)

    def ainvoke(self, messages: list, *args, **kwargs):
        """
        Invoke the agent to start working.

        Args:
            messages: previous messages
        """
        return self.agent.ainvoke(
            {"messages": [{"role": "system", "content": self.prompt}, *messages]}
        )


class AgentFactory:
    def __init__(
        self,
        provider_name: str,  # provider name, eg, deepseek
        model_name: str,
        name: str = "",  # okay, technically, we _dont_ need a name.
        prompt: str = "",
        heartbeat_prompt: str = "",
        agent_type=BaseAgent,
        **kwargs,
    ):
        """
        Create an agent factory
        This'll have the configuration for the agent, which then a Task will actually create the agent, to do things
        So set your config for the agent here.

        Args:
            name: agent nickname
            provider_name: provider_name, eg "deepseek", "openai", "ollama"
            model_name: model_name, eg "deepseek-reasoner", "gpt-5", "llama3.2"
            prompt: prompt for agent
            heartbeat_prompt: prompt for heartbeat
            agent_type: type of agent it spawns
        """

        self.name = name
        self.provider_name = provider_name
        self.model_name = model_name
        self.prompt = prompt
        self.heartbeat_prompt = heartbeat_prompt
        self.kwargs = kwargs
        self.agent_type = agent_type

        self.model = None

    def init_chat_model(self):
        self.model = init_chat_model(
            provider=self.provider_name,
            model=self.model_name,
            **self.kwargs.get("model", {}),
        )

    def create(self):
        """
        Create a BaseAgent object, using some configuration settings
        from this AgentFactory
        """
        if not self.model:
            self.init_chat_model()

        return self.agent_type(
            model=self.model,
            name=self.name,
            prompt=self.prompt,
            heartbeat_prompt=self.heartbeat_prompt,
        )
