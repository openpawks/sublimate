import pytest
from unittest.mock import patch
from src.services.project import ProjectService
from src.schemas.project import ProjectCreate, ProjectUpdate
from src.db import models


class TestProjectService:
    """Test suite for ProjectService."""

    @pytest.fixture
    def project_service(self):
        """Create a fresh ProjectService instance for each test."""
        return ProjectService()

    @pytest.mark.asyncio
    async def test_create_project(self, project_service, async_session, test_user):
        """Test creating a new project."""
        # Mock the get_db dependency
        with patch("src.services.project.get_db_session", return_value=async_session):
            project_create = ProjectCreate(
                name="New Test Project",
                user_id=test_user.id,
                root_dir="/tmp/new_project.git",
                settings_yaml="new: settings",
            )

            result = await project_service.create_project(project_create)

            assert result is not None
            assert result.name == "New Test Project"
            assert result.db_object.user_id == test_user.id
            assert result.db_object.root_dir == "/tmp/new_project.git"

    @pytest.mark.asyncio
    async def test_get_project_by_id(
        self, project_service, async_session, test_project
    ):
        """Test retrieving a project by ID."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            result = await project_service.get_project_by_id(test_project.id)

            assert result is not None
            assert result.db_object.id == test_project.id
            assert result.db_object.name == test_project.name

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, project_service, async_session):
        """Test retrieving a non-existent project returns None."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            result = await project_service.get_project_by_id(9999)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_projects_by_user(
        self, project_service, async_session, test_user, test_project
    ):
        """Test retrieving all projects for a user."""
        # Create another project for the same user
        another_project = models.Project(
            name="Another Project",
            user_id=test_user.id,
            root_dir="/tmp/another_project.git",
            settings_yaml="another: settings",
        )
        async_session.add(another_project)
        await async_session.commit()

        with patch("src.services.project.get_db_session", return_value=async_session):
            result = await project_service.get_projects_by_user(test_user.id)

            assert len(result) >= 2  # Should have at least the two projects
            project_names = [p.db_object.name for p in result]
            assert any(name.startswith("Test Project") for name in project_names)
            assert "Another Project" in project_names

    @pytest.mark.asyncio
    async def test_get_all_projects(self, project_service, async_session, test_project):
        """Test retrieving all projects."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            result = await project_service.get_all_projects()

            assert len(result) >= 1
            assert any(p.db_object.id == test_project.id for p in result)

    @pytest.mark.asyncio
    async def test_update_project(self, project_service, async_session, test_project):
        """Test updating a project."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            project_update = ProjectUpdate(
                name="Updated Project Name",
                user_id=test_project.user_id,
                root_dir="/tmp/updated_project.git",
                settings_yaml="updated: settings",
            )

            result = await project_service.update_project(
                test_project.id, project_update
            )

            assert result is not None
            assert result.db_object.name == "Updated Project Name"
            assert result.db_object.root_dir == "/tmp/updated_project.git"
            assert result.db_object.settings_yaml == "updated: settings"

    @pytest.mark.asyncio
    async def test_update_project_partial(
        self, project_service, async_session, test_project
    ):
        """Test partially updating a project."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            # Only update the name
            project_update = ProjectUpdate(name="Partially Updated Name")

            result = await project_service.update_project(
                test_project.id, project_update
            )

            assert result is not None
            assert result.db_object.name == "Partially Updated Name"
            # Other fields should remain unchanged
            assert result.db_object.root_dir == test_project.root_dir

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, project_service, async_session):
        """Test updating a non-existent project returns None."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            project_update = ProjectUpdate(name="Nonexistent Project")

            result = await project_service.update_project(9999, project_update)

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_project(self, project_service, async_session, test_project):
        """Test deleting a project."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            # First verify project exists
            result = await project_service.get_project_by_id(test_project.id)
            assert result is not None

            # Delete the project
            delete_result = await project_service.delete_project(test_project.id)
            assert delete_result is True

            # Verify project no longer exists
            result = await project_service.get_project_by_id(test_project.id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_service, async_session):
        """Test deleting a non-existent project returns False."""
        with patch("src.services.project.get_db_session", return_value=async_session):
            result = await project_service.delete_project(9999)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_base_project_by_id(self, project_service, test_project):
        """Test getting project from memory cache."""
        # First add project to memory
        project_service.projects_in_memory[test_project.id] = "mock_project_object"

        result = project_service.get_base_project_by_id(test_project.id)
        assert result == "mock_project_object"

    @pytest.mark.asyncio
    async def test_get_base_project_by_id_not_found(self, project_service):
        """Test getting non-existent project from memory returns None."""
        result = project_service.get_base_project_by_id(9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_filesafe_name_validation(self):
        """Test filesafe name validation in task creation."""
        # This would be tested through the task service, not project service
        # Project names don't have filesafe requirements in the schema
        pass
