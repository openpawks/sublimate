from src.orchestration.task import create_task

from src.backend import models

from src.services.task import task_service
from src.schemas.task import TaskCreate

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
        self.repo = None
        self.repos = {}

    def init_repo(self):
        try:
            repo = git.Repo(self.db_object.root_dir)  # (bare)
            assert repo.bare
            return repo
        except NoSuchPathError:
            root_dir = self.db_object.root_dir
            print(f"NoSuchPathError, no repo at {root_dir}, creating new one")

            # make directories
            os.makedirs(root_dir, exist_ok=True)
            # create bare repo
            repo = git.Repo.init(root_dir, bare=True)
            self.repo = repo
            # write first commit (you have to)
            repo.git.worktree("add", "main")
            # write a dummy file for first commit
            with open(os.path.join(root_dir, "main", "README.md"), "w") as f:
                f.write(f"# Hello from {self.db_object.name or 'no name'}")
            # stage all changes for our commit
            repo.index.add("*")
            # commit
            repo.index.commit("Initial commit")
            # now clean up, for other agents and such
            repo.git.worktree("remove", "main")
            os.makedirs(os.join(root_dir, "sublimate"), exist_ok=True)
            # also add a dev branch
            repo.git.worktree("add", "-b", "dev", "sublimate/dev", "main")
            return repo
        except AssertionError:
            raise AssertionError(
                "Your repo is not a 'bare' repo (needs to be able to work with worktrees)"
            )

    def get_dev_worktree_repo(self):
        """
        Get the "regular" repo for dev
        """
        dev_repo = self.repos.get("dev")
        if dev_repo:
            return dev_repo
        else:
            dev_repo = git.Repo(
                os.path.join(self.db_object.root_dir, "sublimate", "dev")
            )
            self.repos.dev = dev_repo
            return dev_repo

    def get_repo(self):
        if self.repo:
            return self.repo
        else:
            return self.init_repo()

    def create_task(self, name=str, branches_from="dev", settings_yaml=""):
        """
        Create a task, calling task_service to create task, but automatically set
        root_dir to the worktree root & automatically set project to this project's id
        """
        # TODO: version control every time a new task is created
        # - task permission control here!
        # WARNING: agents might be able to still write and
        # run a script that works outside of the cwd
        # so we need to write fixes for that

        # TODO: verify file/branch safe name or convert to
        # WARNING: no file/branch safe name rn, please implement

        self.get_repo().git.worktree(
            "add",
            "-b",
            f"{name}",
            f"sublimate/{name}",
            f"{branches_from}",  # or where-ever we are branching from
        )

        # create new worktree
        task = task_service.create_task(
            task=TaskCreate(
                name=name,
                project_id=self.db_object.id,
                root_dir=os.path.join(self.db_object.root_dir, "sublimate", f"{name}"),
                settings_yaml=settings_yaml,
            )
        )

        return task

    def load_task_from_messages(self, messages, id):
        if self.get_task_by_id(id):
            raise ValueError(f"Task #{id} already exists!")
            return

        new_task = create_task(self, messages)

        new_task.id = id
        self.tasks[id] = new_task

        return new_task
