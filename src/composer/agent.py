from langchain.models import init_chat_model
from langchain.agents import create_agent

# base agent
class BaseAgent():
    def __init__(self, llm_config, tools=[]):
        self.prompt = ""
        self.heartbeat = ""
        self.context = ""
        self.dependencies = set({})
        self.model = init_chat_model(
            **llm_config
        )
        self.get_chat_history = lambda x: [] 

        self.agent = create_agent(
            model=self.model,
            tools=tools
        )

    def add_dependency(agent:BaseAgent):
        return self.dependencies.add(agent)

    def invoke():
        message_history = get_chat_history()



