from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    user_id: int = Field(
        description="""user that created the project
                For now, in testing, this can be a single user application, so
                when everything's created, there should just be one user,
                just a dummy user with userid 0"""
    )
    root_dir: str = Field(
        description="where the project will be saved on the filesystem eg: /path/to/project.git/ (because it is bare)"
    )


class ProjectCreate(ProjectBase):
    name: str = Field(min_length=1, max_length=50, description="Name of the project")
    settings_yaml: str | None = Field(
        min_length=0, max_length=2048, description="optional extra settings"
    )


class ProjectUpdate(ProjectBase):
    user_id: int | None = Field(default=None)
    root_dir: str | None = Field(default=None)
    name: str | None = Field(
        min_length=1, max_length=50, description="Name of the project", default=None
    )
    settings_yaml: str | None = Field(
        min_length=0,
        max_length=2048,
        description="optional extra settings",
        default=None,
    )
