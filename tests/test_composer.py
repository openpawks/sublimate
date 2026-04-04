import pytest

import langchain.models import init_chat_model

from unittest.mock import patch

from dotenv import load_dotenv
import os

from src.composer import composer

# params to test
agent_homes = ["./agent_templates/default/"]
project_root_folder = "./tmp/tests/"

class TestBaseAgent():
    def setup_method(self, method):
        self.agent = composer.BaseAgent(
            "coder", # TODO: paramaterize
            agent_homes[0],
            init_chat_model(
                "ollama:qwen3.5:0.8b" # TODO: properly mock this lmao
            ),
            [], # no tools
            project_root_folder
        )

    def teardown_method(self, method):
        pass # apparently handled automatically im not sure...

    def test_load_agent():
        self.agent.load_agent()
        assert all([
            self.agent.name,
            self.agent.prompt,
            self.agent.context,
            self.agent.model,
        ])
        assert self.agent.agent_home == agent_home[0]
        assert self.agent.root_folder == project_root_folder

    def test_format_message_history():
        # TODO: assertion
        self.agent.format_message_history() 

    # are these really necessary?
    def test_invoke():
        assert self.agent.invoke() == "Mocked agent.invoke()"

    def test_ainvoke():
        pass

class TestBaseComposer():
    def setup_method(self, method):
        self.composer = composer.BaseComposer(
            agent_homes[0], # TODO: parameterize
            {}, # no tools rn
        ) 

    def teardown_method(self):
        pass

    # tests go here.
    def test_init_chat_models(self):
        pass

    def test_init_agents(self):
        pass


class TestHeartbeatComposer():
    def setup_method(self, method):
        self.composer = composer.HeartbeatComposer(
            agent_homes[0],
            {}
        )

    def teardown_method():
        pass

    # future
    @pytest.mark.skip(reason="Not implemented")
    def up():
        pass

class TestPipelineComposer():
    def setup_method(self, method):
        self.composer = composer.PipelineComposer(
            agent_homes[0],
            {}
        )

    def teardown_method():
        pass

    # future
    @pytest.mark.skip(reason="Not implemented")
    def up():
        pass
