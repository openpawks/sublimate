from langchain.models import init_chat_model
from langchain.agents import create_agent

from pathlib import Path
import os, glob, yaml

# base task, handles for issues
class BaseTask():
    def __init__(self):
        return

# base agent
class BaseAgent():
    def __init__(self,
        name:str,
        agent_home,
        model,
        tools=[]
    ):
        self.name = ""
        self.prompt = ""
        self.heartbeat = ""
        self.model = model
        self.context = []
        self.agent_home = Path(agent_home)
        self.dependencies = set({})
        self.get_chat_history = lambda x: [] 

        self.agent = create_agent(
            model=self.model,
            tools=tools
        )

    def add_dependency(agent:BaseAgent):
        return self.dependencies.add(agent)
    
    def load_file(self, field, filepath): # intent to set heartbeat, prompt & context
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                setattr(self, field, f.read())
            return
        raise FileNotFoundError

    def load_files(self, files_to_load):
        for field, filepath in files_to_load:
            self.load_file(field, filepath)

    def load_file_for(self, context, filepath): # intent to set heartbeat, prompt & context
        if os.path.exists(filepath, encoding="utf-8"):
            with open(filepath) as f:
                context.append((filepath, f.read()))
        return context
    
    def load_files_for(self, context, filepaths): # we _could_ load async...
        for filepath in filepaths:
            self.load_file_for(context, filepath)
        return context

    def load_agent(self, agent_home):
        agent_home = self.agent_home
        # TODO: compatibility with similar filepaths, heartbeats/{self.name}.md
        self.load_files((
            (agent_home / f"{self.name}.md", "prompt"),
            (agent_home / "heartbeats" / f"{self.name}.md", "heartbeat")
        ))

        # TODO: compatibility with similar filenames like agent.md, AGENT.md, agents.md etc.
        self.load_files_for(self.context, (
            agent_home / ".." / "AGENTS.md",
            agent_home / ".." / "README.md",
            *glob.glob(agent_home / ".." / "docs" / "*", recursive=True)
        )) 

    # TODO: for dependencies, check agent_states to see if it has a report of what has been done from dependent agents.
    
    def format_message_history(
            message_history:list,
            include_prompt=True,
            include_heartbeat=True,
            include_context_files=True,
            include_dependencies=True
    ):

        prompt_prefixes = [
            include_prompt and self.prompt,
            include_heartbeat and self.heartbeat,
            include_context_files and "\n".join(
                [f"{filepath}\n```{file_content}```", for filepath, file_content in self.context]
            ),
            include_dependencies and "\n".join(
                [f"{filepath}\n```{file_content}```", for filepath, file_content in self.load_files_for(
                    [], 
                    [
                        item for sublist
                        in [glob.glob(self.agent_home / "states" / f"{dependency.name}.md" for dependency in self.dependencies)] 
                        for item in sublist
                    ]
                )]
            )
        ]

        return {
            "messages" : [
                *[{"role": "system", "content": x} for x in prompt_prefixes if x],
                *message_history
            ]
        }

    def invoke(message_history:list, **kwargs): # maybe wait for dependencies? how? idk...
        return self.agent.invoke(
            format_message_history(
                message_history, 
                **kwargs
            )
        )

    def ainvoke(message_history:list, **kwargs):
        return self.agent.ainvoke(
            format_message_history(
                message_history, 
                **kwargs
            )
        )

# this should parse a sublimate-compose.yml
class Composer(): 
    def __init__(self, filepath, agent_home, tools:dict):
        self.agent_home = agent_home

        self.agents = []
        self.model = {}

        # TODO: find out how we will add tools to this... (theyre just a dict[str:function])
        self.tools = tools

        with open(filepath) as f:
            self.data = yaml.safe_load(filepath)

        # check it's formatted correctly - needs
        # models
        # agents
        # heartbeats OR pipeline...
        if not all([
            "models" in self.data.keys(),
            "agents" in self.data.keys(),
            "heartbeats" in self.data.keys() or "pipeline" in self.data.keys()
        ]):
            raise KeyError("You need to have: models, agents and either heartbeats OR a pipeline to run compose.")

    def fetch_api_key_for_provider(self, provider:str) -> str:
        # TODO:
        # might have to get this from db not sure...
        pass
    
    def init_chat_model(self, model_data):
        self.models[model] = init_chat_model(
            **model_data,
            api_key=self.fetch_api_key_for_provider(
                model_data.get(
                    "model_provider",
                    model_data.get("model", ":").split(":")[0],
                )
            )
        )

    def init_chat_models(self):
        for model in self.data.get("models").keys():
            self.init_chat_model(
                self.data.get("models").get(model)
            )

    def init_agent(self, agent_data, Agent=BaseAgent):
        self.agents[agent] = Agent(
            agent,
            self.agent_home,
            self.models[agent_data.get(
                "model", 
                agent_data.get("model_name", "default")
            )],
            [tool for tool in [
                self.tools.get(x, None) 
                for x in agent_data.get("tools")
            ] if tool] # probably a better way to do this but your boy's a moron
        )

    def init_agents(self, Agent=BaseAgent):
        for agent in self.data.get("agents").keys():
            self.init_agent(
                self.data.get("agents").get(agent),
                Agent
            )

    def compose(self):
        # TODO: oh god
        pass

class HeartbeatComposer(Composer):
    pass

class PipelineComposer(Composer):
    pass



