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
    def __init__(self,
        name:str,
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
            isinstance(agent_home, Path) and 
            agent_home or 
            Path(agent_home)
        )
        self.root_folder = (
            root_folder and (
                isinstance(agent_home, Path) and 
                agent_home or 
                Path(agent_home)
            ) or
            agent_home / ".."
        )
        self.agent_file_paths = [
            (self.agent_home / f"{self.name}.md", "prompt"),
            (self.agent_home / "heartbeats" / f"{self.name}.md", "heartbeat")
        ]
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

    def load_agent(self):
        # TODO: compatibility with similar filepaths, heartbeats/{self.name}.md
        self.load_files(self.agent_file_paths)

        # TODO: compatibility with similar filenames like agent.md, AGENT.md, agents.md etc.
        self.load_files_for(self.context, (
            self.root_folder / "AGENTS.md",
            self.root_folder / "README.md",
            *glob.glob(self.root_folder / ".." / "docs" / "*", recursive=True)
        )) 

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
class BaseComposer(): 
    """
        So a composer should organise the agents,
        What I want it to be able to do is read a configuration file, and then it'll just run

        The name i've dubbed for this configuration file is sublimate-compose.yml 

        So it'll manage agents... And stuff.

        If you want a projects agents to do something differently, you'll have to stop and start this.
        But it's on heartbeats anyway so no problems.

        Server doesn't need to interact with this directly, just can manage the config files for the agents and composer.
    """
    def __init__(self, agent_home, tools:dict, root_folder=""):
        self.agent_home = (
            isinstance(agent_home, Path) and 
            agent_home or 
            Path(agent_home)
        )
        self.root_folder = (
            root_folder and (
                isinstance(agent_home, Path) and 
                agent_home or 
                Path(agent_home)
            ) or
            agent_home / ".."
        )

        self.agents = []
        self.model = {}

        # TODO: find out how we will add tools to this... (theyre just a dict[str:function])
        self.tools = tools

        with open(agent_home / "sublimate-compose.yml") as f:
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
        # can run tests with mock i guess.
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
        # TODO: add support for param to set different:
        # heartbeat path (currently read from agent_home/heartbeats/name.md)
        # agent path (currently read from agent_home/name.md)
        # state? path (currently only read from agent_home/states/dependency_name.md) [Low importance]
        
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
            ] if tool], # probably a better way to do this but your boy's a moron
            self.root_folder,
        )

        self.agents[agent].load_agent(self.agent_home)


    def init_agents(self, Agent=BaseAgent):
        for agent in self.data.get("agents").keys():
            self.init_agent(
                self.data.get("agents").get(agent),
                Agent
            )

    def run_agent(self, name:str):
        # TODO: agent invoke or something, and also write output to agent/states/agent_name.md
        # should also ideally log this to the db for more logs and potentially better output...
        # i want version control aswell... unsure on how to achieve this (can use git python i know.)
        pass

    def up(self):
        # TODO: oh god
        pass

    def down(self):
        # TODO: ohh goddddd
        pass

class HeartbeatComposer(BaseComposer):
    """
    Much like composer, but will run the agents on a cronjob according to the config.
    """
    pass

class PipelineComposer(BaseComposer):
    """
    Much like composer, but will run agents according to order in pipeline:list param
    """
    pass



