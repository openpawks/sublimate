from src.orchestration.task import create_task

from src.backend import models

import os

import git
from git.exc import NoSuchPathError


class BaseProject:
    """
    The BaseProject object should manage the
    - saving of tasks, agents, chat and such
    - runtime creation of agents
    - runtime creation of tasks
      - git worktrees for each task aswell
    - syncing dependency (task, chat, agent and such) data to the database
    - syncing settings data to the runtime
    - deletion of projects.
    and such

    Will make helper functions to create projects.

    This is intended to be used by the database & fastapi server
    This will hopefully abstract some of the more complicated and nuanced code within tasks, messages and such, however in order to
    save a lot of that data to the database, that might be neccessary
    """

    def __init__(
        self,
        db_object: models.Project,
    ):
        self.db_object = models.Project
        self.root_dir = self.db_object.root_dir  # root_dir

        self.repo = None

    def init_repo(self):
        try:
            repo = git.Repo(self.root_dir)  # (bare)
            assert repo.bare
            return repo
        except NoSuchPathError:
            os.makedirs(self.root_dir, exist_ok=True)
            return git.Repo.init(self.root_dir, bare=True)
        except AssertionError:
            raise AssertionError(
                "Your repo is not a 'bare' repo (needs to be able to work with worktrees)"
            )

    def new_task_id(self):
        return max(list(self.tasks.keys()) or [0]) + 1

    def get_task_by_id(self, id):
        return self.tasks.get(id, None)

    def create_task(self, task_id=-1, messages: list = [], userid=0):
        # TODO: version control every time a new task is created
        # - task permission control here!
        # WARNING: agents might be able to still write and
        # run a script that works outside of the cwd
        # so we need to write fixes for that

        # new_task = create_task(self, messages or [BaseMessage("user", prompt, userid)])

        # new_task.id = self.new_task_id()
        # self.tasks[new_task.id] = new_task

        # return new_task
        pass

    def load_task_from_messages(self, messages, id):
        if self.get_task_by_id(id):
            raise ValueError(f"Task #{id} already exists!")
            return

        new_task = create_task(self, messages)

        new_task.id = id
        self.tasks[id] = new_task

        return new_task
