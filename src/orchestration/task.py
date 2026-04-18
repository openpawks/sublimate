from src.orchestration.chat import BaseChat
from src.orchestration.agent import AgentFactory
from src.orchestration.tools import _create_tool


class BaseTask:
    def __init__(self, project, root_dir, chat, name=""):
        """
        Creates a BaseTask object.
        The BaseTask object invokes agents until they finish their task
        """
        self.project = project
        self.root_dir = root_dir
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
        ]

        if len(self.agents) > 1:
            self.task_tools = [
                *self.task_tools,
                self.next_agent,
                self.set_active_agent,
                self.list_agents_as_text,
            ]

        # TODO: verify this works - wrap so they're callable by langchain... hopefully.
        self.task_tools = [_create_tool(x) for x in self.task_tools]

        # clear all agents,
        for agent in self.agents.values():
            agent.agent = None

    def init_agent(self, agent):
        """
        Langchain's create_agent function, but task specific tools
        """
        agent.init_agent(tools=[*self.task_tools, *agent.tools])

    # TASK SPECIFIC TOOLS
    def read_todos(self):
        """Read todo list"""
        return self.todos

    def edit_todos(self, todos: str):
        """Write/edit todo list, rewrite the whole thing, with marks for what has already been done."""
        self.todos = todos
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
        if not self.active_agent_name or self.active_agent_name not in self.agents:
            # No active agent, set to first agent if any
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
            self.set_active_agent(keys[0])  # wrap around
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
        new_agent = agent_factory.create()
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
        self.invoke_agent(agent, *args, **kwargs)

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

    def close(self):
        self.open = False

    async def repeat_until_complete(self, max_iterations: int = 100):
        """
        Repeat this task, until the agent requests to stop

        Args:
            max_iterations: How many messages until it stops automatically
        """
        self.repeating_until_complete = True
        iteration = 0

        while (
            self.repeating_until_complete and self.open and iteration < max_iterations
        ):
            agent = self.get_active_agent()
            output = await self.invoke_agent()

            self.chat.add_message(
                # TODO: add id
                role="assistant",
                content=output.content,
                username=agent.name,
            )
            iteration += 1

            if iteration >= max_iterations:
                # Safety: stop repeating if we hit max iterations
                self.repeating_until_complete = False
                self.chat.add_message(
                    role="system",
                    content=f"Stopped after {max_iterations} iterations (safety limit).",
                    username="system",
                )

        return


def create_task(project, messages, chat=BaseChat):
    return BaseTask(project, chat.from_messages(messages))
