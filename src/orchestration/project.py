from src.schemas.data import ProjectData, is_filesafe
from src.schemas.task import TaskCreate, TaskUpdate

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
        data: ProjectData,
    ):
        self._data = data
        self.repo = None
        self.repos = {}

    @property
    def name(self):
        return self._data.name

    @property
    def id(self):
        return self._data.id

    @property
    def root_dir(self):
        return self._data.root_dir

    def init_repo(self):
        """
        Attempt to try to find the (bare) repo from the project dir,
        if its not there, then create one.

        If the repo isn't bare, then raise an error
        """
        try:
            repo = git.Repo(self._data.root_dir)
            assert repo.bare
            return repo
        except NoSuchPathError:
            root_dir = self._data.root_dir
            print(f"NoSuchPathError, no repo at {root_dir}, creating new one")

            os.makedirs(root_dir, exist_ok=True)
            repo = git.Repo.init(root_dir, bare=True)
            self.repo = repo
            repo.git.worktree("add", "main")
            with open(os.path.join(root_dir, "main", "README.md"), "w") as f:
                f.write(f"# Hello from {self._data.name or 'no name'}")
            repo.index.add("*")
            repo.index.commit("Initial commit")
            repo.git.worktree("remove", "main")
            os.makedirs(os.path.join(root_dir, "sublimate"), exist_ok=True)
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
                return wt["path"]

        repo = self.get_repo()
        if name in repo.heads:
            worktree_path = os.path.join(self._data.root_dir, "sublimate", name)
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
            dev_repo = git.Repo(os.path.join(self._data.root_dir, "sublimate", "dev"))
            self.repos["dev"] = dev_repo
            return dev_repo

    def get_worktree_repo(self, worktree_name: str):
        """
        Generic get worktree repo function
        """
        cached_repo = self.repos.get(worktree_name)
        if cached_repo:
            return cached_repo

        worktrees = self.get_worktrees()
        worktree_exists = False
        for wt in worktrees:
            if wt["branch"] and wt["branch"].strip("[]") == worktree_name:
                worktree_exists = True
                worktree_path = wt["path"]
                break

        if not worktree_exists:
            raise ValueError(f"Worktree '{worktree_name}' does not exist")

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
        print(
            f"Warning: Version control on task creation not implemented. Creating task '{name}' from branch '{branches_from}'."
        )

        if not is_filesafe(name):
            raise ValueError(
                f"Task name '{name}' is not filesafe. Only alphanumeric, underscores, hyphens, and dots allowed."
            )

        self.get_repo().git.worktree(
            "add",
            "-b",
            f"{name}",
            f"sublimate/{name}",
            f"{branches_from}",
        )

        from src.services import registry

        task = await registry.task_service.create_task(
            task=TaskCreate(
                name=name,
                project_id=self._data.id,
                root_dir=os.path.join(self._data.root_dir, "sublimate", f"{name}"),
                settings_yaml=settings_yaml,
                goal=goal,
            )
        )

        return task

    async def load_task(self, task_id: int, task_name: str):
        """
        Load task from task object, should also ensure that the worktree exists
        if not then create one. Ensure task not closed
        """
        from src.services import registry

        task = await registry.task_service.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        if not task._data.open:
            raise ValueError(f"Task '{task_name}' is closed and cannot be loaded.")

        try:
            worktree_path = self.get_worktree(task_name)
        except ValueError:
            repo = self.get_repo()
            repo.git.worktree(
                "add",
                "-b",
                task_name,
                os.path.join(self._data.root_dir, "sublimate", task_name),
                "dev",
            )
            worktree_path = os.path.join(self._data.root_dir, "sublimate", task_name)
            print(worktree_path)

        return task

    async def close_task(self, task_id: int, task_name: str, auto_merge: bool = False):
        """
        Close task, use task_service to close the task (use udpate function, if not there,
        then someone needs to write that function), remove the worktree.
        """
        from src.services import registry

        updated_task = await registry.task_service.update_task(
            task_id, TaskUpdate(open=False)
        )
        if not updated_task:
            raise ValueError(f"Failed to update task {task_id}")

        repo = self.get_repo()
        worktree_path = os.path.join(self._data.root_dir, "sublimate", task_name)
        if os.path.exists(worktree_path):
            repo.git.worktree("remove", worktree_path)

        if auto_merge:
            await self.merge_task_into_dev(task_name)

    async def merge_task_into_dev(self, task_name: str, auto_resolve: bool = True):
        """
        Merge the task's branch into main. Ensure it passes checks and precomm checks
        If there's a merge conflict, should make a new task to resolve that merge conflict and
        merge that into main

        Args:
            task_name: name of the task/branch to merge
            auto_resolve: automatically create new task if merge conflict
        """
        dev_repo = self.get_dev_worktree_repo()
        branch_name = task_name

        if dev_repo.is_dirty():
            raise RuntimeError(
                "Dev worktree has uncommitted changes. Commit or stash before merging."
            )

        dev_repo.git.checkout("dev")

        try:
            dev_repo.git.merge(branch_name)
            print(f"Successfully merged branch '{branch_name}' into dev.")
        except git.exc.GitCommandError as e:
            print(f"Merge conflict merging '{branch_name}' into dev: {e}")
            if auto_resolve:
                print("Automatically resolving in new branch")
                merge_name = branch_name.strip() + "-resolve-merge-conflict-dev"
                resolve_task = await self.create_task(
                    name=merge_name,
                    goal=f"Resolve merge conflicts from '{branch_name}' into dev",
                    branches_from="dev",
                    settings_yaml="",
                )
                resolve_repo = self.get_worktree_repo(merge_name)
                resolve_repo.git.checkout("dev")
                try:
                    resolve_repo.git.merge(branch_name)
                    print(
                        f"Successfully merged '{branch_name}' into dev in resolve task '{merge_name}'"
                    )
                except git.exc.GitCommandError as merge_error:
                    print(
                        f"Merge conflict in attemptted auto-resolve task merge: {merge_error}"
                    )
                    return resolve_task
                dev_repo.git.merge(merge_name)
                print(f"Successfully merged resolve task '{merge_name}' into dev")
            else:
                dev_repo.git.merge("--abort")
                raise RuntimeError(
                    f"Merge conflict with branch '{branch_name}'. Create a new task to resolve conflicts."
                )

    async def reopen_task(self, task_id: int, task_name: str):
        """
        If a task is closed, then open it, add a worktree to the project
        """
        from src.services import registry

        updated_task = await registry.task_service.update_task(
            task_id, TaskUpdate(open=True)
        )
        if not updated_task:
            raise ValueError(f"Failed to update task {task_id}")

        worktree_path = self.get_worktree(task_name)
        print(worktree_path)
        return updated_task
