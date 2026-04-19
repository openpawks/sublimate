from src.db import models

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
        """
        Attempt to try to find the (bare) repo from the project dir,
        if its not there, then create one.

        If the repo isn't bare, then raise an error
        """
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

    def get_worktrees(self) -> list:
        """
        Get the list of worktrees, GitPython doesn't support this natively
        so we have to write a custom function to parse the string result
        """
        # TODO:
        pass

    def get_branches(self) -> list:
        """
        Get the list of branches
        """
        return self.get_repo().heads

    def get_worktree(self, name: str):
        """
        Get a worktree.
        Get the list of worktrees, see if it exists, if not, then create it (only if theres a branch, of the same name)
        """
        # TODO:
        pass

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

    async def create_task(self, name=str, branches_from="dev", settings_yaml=""):
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

        # create new worktree
        self.get_repo().git.worktree(
            "add",
            "-b",
            f"{name}",
            f"sublimate/{name}",
            f"{branches_from}",  # or where-ever we are branching from
        )

        # create new task
        task = await task_service.create_task(
            task=TaskCreate(
                name=name,
                project_id=self.db_object.id,
                root_dir=os.path.join(self.db_object.root_dir, "sublimate", f"{name}"),
                settings_yaml=settings_yaml,
            )
        )

        return task

    async def load_task(self, task_db_obj: models.Task):
        """
        Load task from task object, should also ensure that the worktree exists
        if not then create one. Ensure task not closed
        """
        # TODO:
        pass

    async def close_task(self, task_db_obj: models.Task, auto_merge: bool = False):
        """
        Close task, use task_service to close the task (use udpate function, if not there,
        then someone needs to write that function), remove the worktree.
        """
        # TODO:

        if auto_merge:
            self.merge_task_into_dev(task_db_obj)

    async def merge_task_into_dev(self, task_db_obj: models.Task):
        """
        Merge the task's branch into main. Ensure it passes checks and precomm checks
        If there's a merge conflict, should make a new task to resolve that merge conflict and
        merge that into main
        """
        # TODO:
        pass

    async def reopen_task(self, task_db_obj: models.Task):
        """
        If a task is closed, then open it, add a worktree to the project
        """
        # TODO:
        pass
