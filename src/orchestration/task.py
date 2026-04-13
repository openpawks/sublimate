from src.orchestration.chat import BaseChat


class BaseTask:
    def __init__(self, project, chat):
        self.project = project
        self.chat = chat
        self.todos = ""

        self.agents = {}

    def get_agent(self, name: str):
        return self.agents.get(name, None)

    def resign_agent(self, agent_name: str):
        if self.get_agent(agent_name):
            del self.agents[agent_name]
            return 1
        else:
            raise KeyError(f"{agent_name} not found")

    def resign_agents(self, agent_names: list):
        for agent_name in agent_names:
            self.resign_agent(agent_name)

    def assign_agent(self, agent):
        if self.get_agent(agent.name):
            print(f"{agent.name} already assigned")
            return None
        self.agents[agent.name] = agent

    def assign_agents(self, agents):
        for agent in agents:
            self.assign_agent(agent)

    def invoke_agent(self, name):
        agent = self.get_agent(name)
        agent.invoke(self.chat.get_messages())

    def get_messages(self, *args, **kwargs):
        return self.chat.get_messages(*args, **kwargs)


def create_task(project, messages, chat=BaseChat):
    return BaseTask(project, chat.from_messages(messages))
