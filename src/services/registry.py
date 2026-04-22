class ServiceRegistry:
    def __init__(self):
        self._services = {}

    def register(self, name: str, service):
        self._services[name] = service

    def get(self, name: str):
        return self._services.get(name)

    @property
    def agent_service(self):
        if "agent" not in self._services:
            from src.services.agent import agent_service

            self._services["agent"] = agent_service
        return self._services["agent"]

    @property
    def chat_service(self):
        if "chat" not in self._services:
            from src.services.chat import chat_service

            self._services["chat"] = chat_service
        return self._services["chat"]

    @property
    def message_service(self):
        if "message" not in self._services:
            from src.services.message import message_service

            self._services["message"] = message_service
        return self._services["message"]

    @property
    def project_service(self):
        if "project" not in self._services:
            from src.services.project import project_service

            self._services["project"] = project_service
        return self._services["project"]

    @property
    def provider_service(self):
        if "provider" not in self._services:
            from src.services.provider import provider_service

            self._services["provider"] = provider_service
        return self._services["provider"]

    @property
    def task_service(self):
        if "task" not in self._services:
            from src.services.task import task_service

            self._services["task"] = task_service
        return self._services["task"]


registry = ServiceRegistry()
