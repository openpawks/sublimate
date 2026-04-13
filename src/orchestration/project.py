from src.orchestration.composer import create_composer
from src.orchestration.tools import get_all_tools
from src.orchestration.task import create_task
from src.orchestration.message import BaseMessage


class BaseProject:
    def __init__(self, root_dir, agent_home):
        self.root_dir = root_dir
        self.agent_home = agent_home
        self.tasks = {}

        self.composer = create_composer(
            agent_home=agent_home,
            tools=get_all_tools(),
            root_dir=root_dir,
            project=self,
        )

    def new_task_id(self):
        return max(list(self.tasks.keys()) or [0]) + 1

    def get_task_by_id(self, id):
        return self.tasks.get(id, None)

    def create_task(self, prompt: str, userid=0):
        # TODO: version control every time a new task is created
        new_task = create_task(self, [BaseMessage("user", prompt, userid)])

        new_task.id = self.new_task_id()
        self.tasks[new_task.id] = new_task

        return new_task

    def load_task_from_messages(self, messages, id):
        if self.get_task_by_id(id):
            raise ValueError(f"Task #{id} already exists!")
            return

        new_task = create_task(self, messages)

        new_task.id = (id,)
        self.tasks[id] = new_task

        return new_task
