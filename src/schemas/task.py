from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=50,
        description="file safe name for the task, will also be used as a git branch name",
    )
    project_id: int
    root_dir: str = Field(
        min_length=1, max_length=256, description="worktree root directory"
    )


class TaskCreate(TaskBase):
    settings_yaml: str | None = Field(
        min_length=0,
        max_length=2048,
        description="optional extra settings",
        default=None,
    )
    todos: str | None = Field(
        min_length=0,
        max_length=512,
        description="short todo list for the AI to remember what to do in a task",
        default=None,
    )
    goal: str | None = Field(
        min_length=1,
        max_length=4096 * 4,
        description="What should this task achieve",
        default=None,
    )


class TaskUpdate(TaskBase):
    name: str | None = Field(
        min_length=1,
        max_length=50,
        description="file safe name for the task, will also be used as a git branch name",
        default=None,
    )
    project_id: int | None = Field(default=None)
    root_dir: str | None = Field(
        min_length=1,
        max_length=256,
        description="worktree root directory",
        default=None,
    )
    open: bool | None = Field(description="is the task open?", default=None)
    settings_yaml: str | None = Field(
        min_length=0,
        max_length=2048,
        description="optional extra settings",
        default=None,
    )
    todos: str | None = Field(
        min_length=0,
        max_length=512,
        description="short todo list for the AI to remember what to do in a task",
        default=None,
    )
