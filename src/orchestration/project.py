from src.db import models

from src.services.task import task_service
from src.schemas.task import TaskCreate, TaskUpdate

import os
import re

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
        self.db_object = db_object
        self.repo = None
        self.repos = {}

    @property
    def name(self):
        return self.db_object.name

    @property
    def id(self):
        return self.db_object.id

    @staticmethod
    def _is_filesafe(name: str) -> bool:
        """
        Check if a string is safe for use as a filename/branch name.
        Allows alphanumeric, hyphens, underscores, dots, no spaces or slashes.
        """
        # Allow alphanumeric, hyphen, underscore, dot
        pattern = r"^[a-zA-Z0-9_.-]+$"
        return bool(re.match(pattern, name))

    @staticmethod
    def _to_filesafe(name: str) -> str:
        """
        Convert a string to be safe for use as a filename/branch name.
        Replaces invalid characters (spaces, slashes, etc.) with hyphens.
        """
        # Replace spaces and slashes with hyphens, remove other non-safe chars
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", name)
        # Collapse multiple hyphens into one
        safe = re.sub(r"-+", "-", safe)
        # Strip leading/trailing hyphens and dots
        safe = safe.strip("-.")
        return safe if safe else "unnamed"

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
            os.makedirs(os.path.join(root_dir, "sublimate"), exist_ok=True)
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
        repo = self.get_repo()
        output = repo.git.worktree("list")
        worktrees = []
        for line in output.splitlines():
            if line.strip():
                parts = line.split()
                if len(parts) >= 1:
                    path = parts[0]
                    commit = parts[1] if len(parts) > 1 else None
                    branch = parts[2] if len(parts) > 2 else None
                    worktrees.append({"path": path, "commit": commit, "branch": branch})
        return worktrees

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
        worktrees = self.get_worktrees()
        for wt in worktrees:
            if wt["branch"] and wt["branch"].strip("[]") == name:
                # Worktree exists, return path
                return wt["path"]

        # No existing worktree, check if branch exists
        repo = self.get_repo()
        if name in repo.heads:
            # Create worktree in sublimate/{name}
            worktree_path = os.path.join(self.db_object.root_dir, "sublimate", name)
            repo.git.worktree("add", "-b", name, worktree_path, name)
            return worktree_path
        else:
            raise ValueError(f"Branch '{name}' does not exist. Cannot create worktree.")
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
            self.repos["dev"] = dev_repo
            return dev_repo

    def get_worktree_repo(self, worktree_name: str):
        """
        Generic get worktree repo function
        """
        # Check if repo is already cached
        cached_repo = self.repos.get(worktree_name)
        if cached_repo:
            return cached_repo

        # Check if worktree exists
        worktrees = self.get_worktrees()
        worktree_exists = False
        for wt in worktrees:
            if wt["branch"] and wt["branch"].strip("[]") == worktree_name:
                worktree_exists = True
                worktree_path = wt["path"]
                break

        if not worktree_exists:
            raise ValueError(f"Worktree '{worktree_name}' does not exist")

        # Create repo object and cache it
        repo = git.Repo(worktree_path)
        self.repos[worktree_name] = repo
        return repo

    def _parse_worktrees_output(self, output: str) -> list:
        """
        Parse the output of git worktree list into structured data
        """
        worktrees = []
        for line in output.splitlines():
            if line.strip():
                parts = line.split()
                if len(parts) >= 1:
                    path = parts[0]
                    commit = parts[1] if len(parts) > 1 else None
                    branch = parts[2] if len(parts) > 2 else None
                    worktrees.append({"path": path, "commit": commit, "branch": branch})
        return worktrees

    def get_repo(self):
        if self.repo:
            return self.repo
        else:
            return self.init_repo()

    async def create_task(
        self, name: str, goal: str, branches_from="dev", settings_yaml=""
    ):
        """
        Create a task, calling task_service to create task, but automatically set
        root_dir to the worktree root & automatically set project to this project's id

        Args:
            name: new task name, branch name etc
            goal: task goal or description
            branches_from: branches from task
            settings_yaml: additional options
        """
        # TODO: version control every time a new task is created - not yet implemented
        # - task permission control here!
        # WARNING: agents might be able to still write and
        # run a script that works outside of the cwd
        # so we need to write fixes for that
        print(
            f"Warning: Version control on task creation not implemented. Creating task '{name}' from branch '{branches_from}'."
        )

        if not self._is_filesafe(name):
            raise ValueError(
                f"Task name '{name}' is not filesafe. Only alphanumeric, underscores, hyphens, and dots allowed."
            )
            # OR WE COULD DO name = self._to_filesafe(name)

        # create new worktree
        # TODO: check task name doesnt already exist in repo/project
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
                goal=goal,
            )
        )

        return task

    async def load_task(self, task_db_obj: models.Task):
        """
        Load task from task object, should also ensure that the worktree exists
        if not then create one. Ensure task not closed
        """
        if not task_db_obj.open:
            raise ValueError(
                f"Task '{task_db_obj.name}' is closed and cannot be loaded."
            )

        # Ensure worktree exists
        try:
            worktree_path = self.get_worktree(task_db_obj.name)
        except ValueError:
            # Branch doesn't exist, create from dev
            repo = self.get_repo()
            repo.git.worktree(
                "add",
                "-b",
                task_db_obj.name,
                os.path.join(self.db_object.root_dir, "sublimate", task_db_obj.name),
                "dev",
            )
            worktree_path = os.path.join(
                self.db_object.root_dir, "sublimate", task_db_obj.name
            )
            print(worktree_path)

        # Return the task object (could be BaseTask)
        # For now just return the db object
        return task_db_obj

    async def close_task(self, task_db_obj: models.Task, auto_merge: bool = False):
        """
        Close task, use task_service to close the task (use udpate function, if not there,
        then someone needs to write that function), remove the worktree.
        """
        # Update task as closed
        updated_task = await task_service.update_task(
            task_db_obj.id, TaskUpdate(open=False)
        )
        if not updated_task:
            raise ValueError(f"Failed to update task {task_db_obj.id}")

        # Remove worktree
        repo = self.get_repo()
        worktree_path = os.path.join(
            self.db_object.root_dir, "sublimate", task_db_obj.name
        )
        if os.path.exists(worktree_path):
            repo.git.worktree("remove", worktree_path)

        if auto_merge:
            await self.merge_task_into_dev(task_db_obj)

    async def merge_task_into_dev(
        self, task_db_obj: models.Task, auto_resolve: bool = True
    ):
        """
        Merge the task's branch into main. Ensure it passes checks and precomm checks
        If there's a merge conflict, should make a new task to resolve that merge conflict and
        merge that into main

        Args:
            task_db_obj
            auto_resolve: automatically create new task if merge conflict
        """
        dev_repo = self.get_dev_worktree_repo()
        branch_name = task_db_obj.name

        # Ensure dev repo is clean
        if dev_repo.is_dirty():
            raise RuntimeError(
                "Dev worktree has uncommitted changes. Commit or stash before merging."
            )

        # Switch to dev branch (already in dev worktree)
        dev_repo.git.checkout("dev")

        # Merge task branch
        try:
            dev_repo.git.merge(branch_name)
            print(f"Successfully merged branch '{branch_name}' into dev.")
        except git.exc.GitCommandError as e:
            # Merge conflict
            print(f"Merge conflict merging '{branch_name}' into dev: {e}")
            # Abort merge
            if auto_resolve:
                print("Automatically resolving in new branch")
                # TODO: verify appropriate name
                # - actually create a new task, containing the merge conflicts,
                # it shouldn't affect dev. if this requires a new function write one.
                merge_name = branch_name.strip() + "-resolve-merge-conflict-dev"
                # Create new task to resolve merge conflicts
                resolve_task = await self.create_task(
                    name=merge_name,
                    goal=f"Resolve merge conflicts from '{branch_name}' into dev",
                    branches_from="dev",
                    settings_yaml="",
                )
                # Get the resolve task repo
                resolve_repo = self.get_worktree_repo(merge_name)
                # Checkout dev in resolve repo
                resolve_repo.git.checkout("dev")
                # Merge the original branch into dev in the resolve repo
                try:
                    resolve_repo.git.merge(branch_name)
                    print(
                        f"Successfully merged '{branch_name}' into dev in resolve task '{merge_name}'"
                    )
                except git.exc.GitCommandError as merge_error:
                    print(
                        f"Merge conflict in attemptted auto-resolve task merge: {merge_error}"
                    )
                    # The resolve task now contains the merge conflicts for manual resolution
                    return resolve_task
                # If merge succeeded in resolve task, merge resolve task back into dev
                dev_repo.git.merge(merge_name)
                print(f"Successfully merged resolve task '{merge_name}' into dev")
            else:
                dev_repo.git.merge("--abort")
                raise RuntimeError(
                    f"Merge conflict with branch '{branch_name}'. Create a new task to resolve conflicts."
                )

    async def reopen_task(self, task_db_obj: models.Task):
        """
        If a task is closed, then open it, add a worktree to the project
        """
        # Update task as open
        updated_task = await task_service.update_task(
            task_db_obj.id, TaskUpdate(open=True)
        )
        if not updated_task:
            raise ValueError(f"Failed to update task {task_db_obj.id}")

        # Ensure worktree exists (will create if branch exists)
        worktree_path = self.get_worktree(task_db_obj.name)
        print(worktree_path)
        return updated_task
