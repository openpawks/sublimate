import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.db.database import Base
from src.db import models


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create async engine for testing with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async session for testing."""
    AsyncSessionLocal = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def db(async_session):
    """Provide database session for tests."""

    async def override_get_db():
        yield async_session

    return override_get_db


@pytest.fixture(autouse=True)
def patch_db_session(monkeypatch, async_session):
    """Patch get_db_session to return the test session."""

    async def mock_get_db_session():
        return async_session

    monkeypatch.setattr("src.db.database.get_db_session", mock_get_db_session)


@pytest.fixture
def test_id(request):
    """Return a unique identifier for each test."""
    # Use test name without brackets and special characters
    test_name = request.node.name.replace("[", "_").replace("]", "_").replace(".", "_")
    return test_name[:50]  # Limit length for database constraints


@pytest_asyncio.fixture(autouse=True)
async def clean_database(async_session):
    """Clean all database tables before each test."""
    # Clean before test runs
    from sqlalchemy import text

    # Disable foreign key checks temporarily
    await async_session.execute(text("PRAGMA foreign_keys = OFF"))

    # Delete all data from tables in dependency order
    tables = [
        "messages",
        "senders",
        "task_to_agent",
        "agents",
        "providers",
        "chats",
        "tasks",
        "projects",
    ]

    for table in tables:
        await async_session.execute(text(f"DELETE FROM {table}"))

    await async_session.execute(text("PRAGMA foreign_keys = ON"))
    await async_session.commit()

    yield

    # After test completes, clean up again to be safe
    # (though next test will clean before running)
    await async_session.execute(text("PRAGMA foreign_keys = OFF"))
    for table in tables:
        await async_session.execute(text(f"DELETE FROM {table}"))
    await async_session.execute(text("PRAGMA foreign_keys = ON"))
    await async_session.commit()


@pytest_asyncio.fixture
async def test_user(async_session, test_id):
    """Create a test user."""
    user = models.User(name=f"testuser_{test_id}", password_hash="hashedpassword123")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_project(async_session, test_user, test_id):
    """Create a test project."""
    project = models.Project(
        name=f"Test Project {test_id}",
        user_id=test_user.id,
        root_dir=f"/tmp/test_project_{test_id}.git",
        settings_yaml="test: settings",
    )
    async_session.add(project)
    await async_session.commit()
    await async_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_provider(async_session, test_id):
    """Create a test provider."""
    provider = models.Provider(
        id=f"test-provider-{test_id}",
        name=f"Test Provider {test_id}",
        api_key=f"test-api-key-123-{test_id}",
    )
    async_session.add(provider)
    await async_session.commit()
    await async_session.refresh(provider)
    return provider


@pytest_asyncio.fixture
async def test_agent(async_session, test_project, test_provider, test_id):
    """Create a test agent."""
    agent = models.Agent(
        name=f"Test Agent {test_id}",
        project_id=test_project.id,
        provider_id=test_provider.id,
        model_name=f"test-model-{test_id}",
        prompt=f"Test agent prompt {test_id}",
        heartbeat_prompt=f"Test heartbeat prompt {test_id}",
        settings_yaml="agent: settings",
    )
    async_session.add(agent)
    await async_session.commit()
    await async_session.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def test_chat(async_session, test_project, test_id):
    """Create a test chat."""
    # First create a task for the chat
    task = models.Task(
        name=f"test-task-{test_id}",
        project_id=test_project.id,
        root_dir=f"/tmp/test_task_{test_id}",
        settings_yaml="task: settings",
        todos="Test todos",
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)

    chat = models.Chat(task_id=task.id)
    async_session.add(chat)
    await async_session.commit()
    await async_session.refresh(chat)

    # Link task to chat
    task.chat_id = chat.id
    await async_session.commit()
    await async_session.refresh(task)

    return chat


@pytest_asyncio.fixture
async def test_task(async_session, test_project, test_id):
    """Create a test task."""
    task = models.Task(
        name=f"test-task-{test_id}",
        project_id=test_project.id,
        root_dir=f"/tmp/test_task_{test_id}",
        settings_yaml="task: settings",
        todos="Test todos",
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)

    # Create chat for task
    chat = models.Chat(task_id=task.id)
    async_session.add(chat)
    await async_session.commit()
    await async_session.refresh(chat)

    # Link task to chat
    task.chat_id = chat.id
    await async_session.commit()
    await async_session.refresh(task)

    return task


@pytest_asyncio.fixture
async def test_message(async_session, test_chat):
    """Create a test message."""
    message = models.Message(
        content="Test message content", role="user", chat_id=test_chat.id
    )
    async_session.add(message)
    await async_session.commit()
    await async_session.refresh(message)
    return message
