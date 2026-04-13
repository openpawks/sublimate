from src.orchestration.chat import BaseChat


class BaseTask:
    def __init__(self, project, chat, name=""):
        self.project = project
        self.chat = chat
        self.todos = ""  # AI can generate checklist etc.
        self.name = name
        self.open = True

        self.task_tools = []

        self.repeating_until_complete = False
        self.active_agent_name = ""
        self.agents = {}

    def refresh_task_tools(self):
        self.task_tools = [
            self.read_todos,
            self.edit_todos,
            self.close_task,
            self.request_human_approval,
            # next agent
            # set active agents
            # list agents
        ]

        if len(self.agents) > 1:
            self.task_tools = [
                *self.task_tools,
                self.next_agent,
                self.set_active_agent,
                self.list_agents_as_text,
            ]

        # reinit all agents
        for agent in self.agents.values():
            agent.init()

    # TASK SPECIFIC TOOLS
    def read_todos(self):
        """Read todo list"""
        return

    def edit_todos(self, todos: str):
        """Write/edit todo list, rewrite the whole thing, with marks for what has already been done."""
        return

    def close_task(self):
        """Close task when you think its done. Do this when you are sure, and tests have passed."""
        # when finished
        self.repeating_until_complete = False
        self.close()
        return

    def request_human_approval(self):
        """Request human approval or human input"""
        # TODO: more
        self.repeating_until_complete = False

    def next_agent(self):
        """Cycle the conversation to the next agent"""
        keys = list(self.agents.keys())
        next_index = keys.index(self.active_agent_name) + 1
        self.set_active_agent(next_index < len(keys) and next_index or keys[0])
        return "Success"

    def set_active_agent(self, name: str):
        """Allow another worker to work on this, should use for todos where another agent is likely more suitable."""
        if name in self.agents.keys():
            self.active_agent_name = ""
        else:
            return f"Agent '{name}' does not exist. The current agents assigned are\n{self.list_agents}"

    def list_agents_as_text(self, name: str):
        """List agents in chat."""
        return "\n".join(list(self.agents.keys()))

    def get_agent(self, name: str):
        return self.agents.get(name, None)

    def get_active_agent(self):
        agent_name = (
            self.active_agent_name
            or len(self.agents.keys())
            and self.agents.keys()[0]
            or None
        )
        if agent_name:
            return self.agents.get(agent_name)
        else:
            raise ValueError("No agents set!")

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
        self.agents[agent.name] = agent.clone().task_agent(self)

    def assign_agents(self, agents):
        for agent in agents:
            self.assign_agent(agent)

    def invoke_agent(self, name):
        agent = self.get_agent(name)
        agent.invoke(self.chat.get_messages())

    def get_messages(self, *args, **kwargs):
        return self.chat.get_messages(*args, **kwargs)

    def was_created_at(self):
        return self.chat.was_created_at()

    def was_last_updated_at(self):
        return self.chat.was_last_updated_at(self)

    def close(self):
        self.open = False

    def repeat_until_complete(self):
        self.repeating_until_complete = True

        while self.repeating_until_complete and self.open:
            output = self.get_active_agent.run()
            self.chat.add_message(
                role="assistant",
                content=output.content,
                username=self.active_agent_name,
            )

        return


def create_task(project, messages, chat=BaseChat):
    return BaseTask(project, chat.from_messages(messages))
