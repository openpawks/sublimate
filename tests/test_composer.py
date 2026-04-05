import pytest

from langchain.chat_models import init_chat_model

from unittest.mock import patch, MagicMock, call, AsyncMock

from dotenv import load_dotenv
import os
import yaml
import asyncio
from datetime import datetime

from src.composer import composer

# params to test
agent_homes = ["./agent_templates/default/"]
project_root_folder = "./tmp/tests/"


class TestBaseAgent:
    def setup_method(self, method):
        self.agent = composer.BaseAgent(
            "coder",  # TODO: paramaterize
            agent_homes[0],
            init_chat_model(
                "ollama:qwen3.5:0.8b"  # TODO: properly mock this lmao
            ),
            [],  # no tools
            project_root_folder,
        )

    def teardown_method(self, method):
        pass  # apparently handled automatically im not sure...

    def test_load_agent(self):
        self.agent.load_agent()
        assert all(
            [
                self.agent.name,
                self.agent.prompt,
                # self.agent.context,
                self.agent.model,
            ]
        )
        # assert self.agent.agent_home == agent_home[0]
        # assert self.agent.root_folder == project_root_folder

    def test_load_file(self):
        # Load existing file
        self.agent.load_file("prompt", self.agent.agent_home / "coder.md")
        assert self.agent.prompt
        # Ensure field set
        # Test FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.agent.load_file("prompt", self.agent.agent_home / "nonexistent.md")

    def test_load_files(self):
        # Test loading multiple files
        files_to_load = [
            ("prompt", self.agent.agent_home / "coder.md"),
            ("heartbeat", self.agent.agent_home / "heartbeats" / "coder.md"),
        ]
        self.agent.load_files(files_to_load)
        assert self.agent.prompt
        assert self.agent.heartbeat

    def test_load_file_for(self):
        context = []
        self.agent.load_file_for(context, self.agent.agent_home / "coder.md")
        assert len(context) == 1
        filepath, content = context[0]
        assert content

    def test_load_files_for(self):
        context = []
        filepaths = [
            self.agent.agent_home / "coder.md",
            self.agent.agent_home / "heartbeats" / "coder.md",
        ]
        self.agent.load_files_for(context, filepaths)
        assert len(context) == 2
        for filepath, content in context:
            assert content

    def test_add_dependency(self):
        # Create another mock agent
        mock_agent = composer.BaseAgent(
            "tester",
            agent_homes[0],
            init_chat_model("ollama:qwen3.5:0.8b"),
            [],
            project_root_folder,
        )
        self.agent.add_dependency(mock_agent)
        assert mock_agent in self.agent.dependencies

    def test_format_message_history(self):
        # TODO: assertion
        self.agent.format_message_history(message_history=[])

    # are these really necessary?
    def test_invoke(self):
        assert self.agent.invoke([]) == "Mocked agent.invoke()"

    def test_ainvoke(self):
        # ainvoke is async; we need to mock it properly
        # The mock fixture already patches ainvoke to return "Mocked agent.ainvoke()"
        # But we need to call it as async; we'll just call it and ignore async nature
        # since the mock is synchronous.
        result = self.agent.ainvoke([])
        assert result == "Mocked agent.ainvoke()"


class TestBaseComposer:
    def setup_method(self, method):
        self.composer = composer.BaseComposer(
            agent_homes[0],  # TODO: parameterize
            {},  # no tools rn
        )

    def teardown_method(self):
        pass

    # tests go here.
    def test_init_chat_models(self):
        self.composer.init_chat_models()

    def test_init_agents(self):
        self.composer.init_chat_models()
        self.composer.init_agents()
        assert self.composer.get_agent("main").name == "main"

    def test_get_agent_names(self):
        names = self.composer.get_agent_names()
        assert isinstance(names, list)
        assert "main" in names
        assert "coder" in names
        assert "tester" in names

    def test_get_heartbeats_from_settings(self):
        heartbeats = self.composer.get_heartbeats_from_settings()
        assert isinstance(heartbeats, dict)
        assert "main" in heartbeats
        assert "schedule" in heartbeats["main"]

    def test_get_pipeline(self):
        pipeline = self.composer.get_pipeline()
        assert pipeline == {}

    def test_get_models(self):
        self.composer.init_chat_models()
        models = self.composer.get_models()
        assert isinstance(models, dict)
        assert len(models) > 0

    def test_get_model(self):
        self.composer.init_chat_models()
        model = self.composer.get_model("favorite-model")
        assert model is not None

    def test_get_agent(self):
        self.composer.init_chat_models()
        self.composer.init_agents()
        agent = self.composer.get_agent("main")
        assert agent is not None
        assert agent.name == "main"
        # Test missing agent returns None
        assert self.composer.get_agent("nonexistent") is None

    def test_missing_config_raises(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                composer.BaseComposer(tmpdir, {})

    def test_missing_keys_raises(self):
        import tempfile
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "sublimate-compose.yml")
            # Write config missing models
            with open(config_path, "w") as f:
                yaml.dump({"agents": {}}, f)
            with pytest.raises(KeyError):
                composer.BaseComposer(tmpdir, {})
            # Write config missing agents
            with open(config_path, "w") as f:
                yaml.dump({"models": {}}, f)
            with pytest.raises(KeyError):
                composer.BaseComposer(tmpdir, {})
            # Write config with heartbeats but missing models
            with open(config_path, "w") as f:
                yaml.dump({"agents": {}, "heartbeats": {}}, f)
            with pytest.raises(KeyError):
                composer.BaseComposer(tmpdir, {})


class TestHeartbeat:
    def setup_method(self, method):
        # Mock agent
        self.mock_agent = MagicMock()
        self.mock_agent.invoke.return_value = "invoke result"
        self.mock_agent.ainvoke.return_value = "ainvoke result"
        self.heartbeat = composer.Heartbeat(self.mock_agent, "* * * * *")

    @patch("src.composer.composer.datetime")
    @patch("src.composer.composer.croniter")
    def test_get_next(self, mock_croniter, mock_datetime):
        mock_now = datetime(2025, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_iter = MagicMock()
        mock_croniter.return_value = mock_iter
        result = self.heartbeat.get_next()
        mock_croniter.assert_called_once_with("* * * * *", mock_now)
        assert result == mock_iter

    @patch("src.composer.composer.datetime")
    @patch("src.composer.composer.asyncio.sleep", new_callable=AsyncMock)
    def test_wait_until_datetime(self, mock_sleep, mock_datetime):
        mock_now = datetime(2025, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = mock_now
        target = datetime(2025, 1, 1, 0, 1, 0)
        _ = self.heartbeat.wait_until_datetime(target)
        mock_sleep.assert_called_once_with(60.0)

    @patch("src.composer.composer.datetime")
    @patch("src.composer.composer.asyncio.sleep", new_callable=AsyncMock)
    def test_wait_until_datetime_past(self, mock_sleep, mock_datetime):
        mock_now = datetime(2025, 1, 1, 0, 1, 0)
        mock_datetime.now.return_value = mock_now
        target = datetime(2025, 1, 1, 0, 0, 0)
        _ = self.heartbeat.wait_until_datetime(target)
        mock_sleep.assert_called_once_with(0)

    def test_get_task_context_as_messages(self):
        messages = self.heartbeat.get_task_context_as_messages()
        assert messages == []

    def test_beat(self):
        self.heartbeat.beat()
        self.mock_agent.invoke.assert_called_once_with([])

    def test_abeat(self):
        self.heartbeat.abeat()
        self.mock_agent.ainvoke.assert_called_once_with([])

    def test_start_stop(self):
        # Mock daemon coroutine
        with patch.object(
            self.heartbeat, "daemon", new_callable=AsyncMock
        ) as mock_daemon:
            mock_task = MagicMock()
            with patch(
                "src.composer.composer.asyncio.create_task", return_value=mock_task
            ) as mock_create:
                task = self.heartbeat.start()
                assert task == mock_task
                assert self.heartbeat.current == mock_task
                mock_create.assert_called_once()
                args, _ = mock_create.call_args
                assert asyncio.iscoroutine(args[0])
                # Test double start raises RuntimeError
                with pytest.raises(RuntimeError):
                    self.heartbeat.start()
                # Stop
                result = self.heartbeat.stop()
                assert result == mock_task.cancel.return_value
                mock_task.cancel.assert_called_once()
                # Stop again returns None
                self.heartbeat.current = None
                assert self.heartbeat.stop() is None


class TestHeartbeatComposer:
    def setup_method(self, method):
        self.composer = composer.HeartbeatComposer(agent_homes[0], {})

    def teardown_method(self):
        pass

    def test_init_heartbeats(self):
        self.composer.init_chat_models()
        self.composer.init_agents()
        self.composer.init_heartbeats()
        # Should have heartbeats for main, coder, tester
        assert "main" in self.composer.heartbeats
        assert "coder" in self.composer.heartbeats
        assert "tester" in self.composer.heartbeats
        heartbeat = self.composer.get_heartbeat("main")
        assert heartbeat is not None
        assert heartbeat.agent.name == "main"
        assert heartbeat.cron == "* 1 * * *"

    def test_get_active_inactive_heartbeats(self):
        self.composer.init_chat_models()
        self.composer.init_agents()
        self.composer.init_heartbeats()
        active = self.composer.get_active_heartbeats()
        inactive = self.composer.get_inactive_heartbeats()
        assert active == []
        assert len(inactive) == 3
        # Simulate starting a heartbeat
        with patch.object(self.composer.heartbeats["main"], "start") as mock_start:
            mock_task = MagicMock()
            mock_start.return_value = mock_task
            self.composer.start_heartbeat("main")
            mock_start.assert_called_once()
            # Now active should have one? Actually active list checks hb.current
            # We need to set current manually
            self.composer.heartbeats["main"].current = mock_task
            active = self.composer.get_active_heartbeats()
            assert len(active) == 1
            inactive = self.composer.get_inactive_heartbeats()
            assert len(inactive) == 2

    def test_start_stop_heartbeat(self):
        self.composer.init_chat_models()
        self.composer.init_agents()
        self.composer.init_heartbeats()
        heartbeat = self.composer.heartbeats["main"]
        with patch.object(heartbeat, "start") as mock_start:
            mock_task = MagicMock()
            mock_start.return_value = mock_task
            result = self.composer.start_heartbeat("main")
            mock_start.assert_called_once()
            assert result == mock_task
        with patch.object(heartbeat, "stop") as mock_stop:
            mock_stop.return_value = True
            result = self.composer.stop_heartbeat("main")
            mock_stop.assert_called_once()
            assert result == True

    def test_up(self):
        self.composer.init_chat_models()
        self.composer.init_agents()
        self.composer.init_heartbeats()
        with patch.object(self.composer, "start_heartbeat") as mock_start:
            self.composer.up()
            # Should call start_heartbeat for each heartbeat in settings
            assert mock_start.call_count == 3
            calls = [call("main"), call("coder"), call("tester")]
            mock_start.assert_has_calls(calls, any_order=True)


class TestPipelineComposer:
    def setup_method(self, method):
        self.composer = composer.PipelineComposer(agent_homes[0], {})

    def teardown_method(self):
        pass

    # future
    @pytest.mark.skip(reason="Not implemented")
    def up():
        pass
