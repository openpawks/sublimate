# Mocking Database for Tests

This guide explains how to write tests that interact with the database in the Sublimate project. The test suite uses pytest with async SQLAlchemy and SQLite in-memory database.

## Overview

- **In-memory SQLite database**: Each test session creates a temporary SQLite database in memory (`sqlite+aiosqlite:///:memory:`).
- **Table creation**: All tables are created once per session using SQLAlchemy's `Base.metadata.create_all`.
- **Fixture-based session management**: Each test gets a fresh `AsyncSession` that shares the same engine.
- **Automatic cleanup**: Data is deleted from all tables before and after each test.
- **Global patching**: The `get_db_session` function from `src.db.database` is patched to return the test session.
- **Service-level patching**: Some tests also patch the imported `get_db_session` reference in individual service modules.

## Key Fixtures

### `async_engine`

Session-scoped fixture that creates an async engine connected to an in-memory SQLite database. It creates all tables at startup and drops them at teardown.

```python
@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

### `async_session`

Fixture that yields an `AsyncSession` bound to the test engine. Used by most tests to interact with the database.

```python
@pytest_asyncio.fixture
async def async_session(async_engine):
    AsyncSessionLocal = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session
```

### `patch_db_session`

**Autouse fixture** that patches `src.db.database.get_db_session` to return the test session. This ensures that any code that calls `get_db_session()` (including service methods) will use the same in-memory database.

```python
@pytest.fixture(autouse=True)
def patch_db_session(monkeypatch, async_session):
    async def mock_get_db_session():
        return async_session
    monkeypatch.setattr("src.db.database.get_db_session", mock_get_db_session)
```

**Important**: Because some service modules import `get_db_session` at the module level (e.g., `from src.db.database import get_db_session`), the global patch may not affect those references. In such cases, you must also patch the imported reference in the service module (see [Service-Level Patching](#service-level-patching)).

### `clean_database`

**Autouse fixture** that deletes all rows from all tables before each test (and also after each test for safety). It temporarily disables foreign key constraints to allow deletion in any order.

```python
@pytest_asyncio.fixture(autouse=True)
async def clean_database(async_session):
    from sqlalchemy import text
    await async_session.execute(text("PRAGMA foreign_keys = OFF"))
    tables = [
        "messages", "senders", "task_to_agent", "agents",
        "providers", "chats", "tasks", "projects", "users"
    ]
    for table in tables:
        await async_session.execute(text(f"DELETE FROM {table}"))
    await async_session.execute(text("PRAGMA foreign_keys = ON"))
    await async_session.commit()
    yield
    # Cleanup after test (optional)
```

### Data Fixtures

Several fixtures create ready‑to‑use test objects:

- `test_user` – a `User` instance
- `test_project` – a `Project` linked to the user
- `test_provider` – a `Provider` instance
- `test_agent` – an `Agent` linked to a project and provider
- `test_task` – a `Task` with an associated `Chat`
- `test_chat` – a `Chat` linked to a task
- `test_message` – a `Message` in a chat

Each fixture uses the `test_id` fixture to generate unique names/IDs, preventing conflicts between tests.

## Writing a Database Test

### Basic Pattern

```python
import pytest
from unittest.mock import patch
from src.services.task import TaskService
from src.schemas.task import TaskCreate

class TestTaskService:
    @pytest.fixture
    def task_service(self):
        return TaskService()

    @pytest.mark.asyncio
    async def test_create_task(self, task_service, async_session, test_project):
        # Patch the service's own get_db_session reference
        with patch("src.services.task.get_db_session", return_value=async_session):
            # Also patch other services that may be called (e.g., message_service)
            with patch("src.services.message.get_db_session", return_value=async_session):
                # Mock any external service calls
                mock_project = AsyncMock()
                mock_project.db_object = test_project
                with patch(
                    "src.services.project.project_service.get_project_by_id",
                    return_value=mock_project,
                ):
                    task_create = TaskCreate(...)
                    result = await task_service.create_task(task_create)
                    assert result is not None
```

### Service‑Level Patching

Because `src.services.message` imports `get_db_session` at the module level, the global `patch_db_session` fixture does **not** affect it. You must patch the reference inside the service module:

```python
with patch("src.services.message.get_db_session", return_value=async_session):
    # Now message_service will use the test session
```

The same applies to any service that uses a module‑level import of `get_db_session`. Check the service's source file to see whether it imports `get_db_session` from `src.db.database` or uses `src.db.database.get_db_session` directly.

### Creating Test Data

Use the existing data fixtures (`test_project`, `test_user`, etc.) whenever possible. If you need a custom object, add it directly to the session:

```python
task = models.Task(
    name="custom-task",
    project_id=test_project.id,
    root_dir="/tmp/custom",
    settings_yaml="custom: settings",
)
async_session.add(task)
await async_session.commit()
await async_session.refresh(task)
```

### Cleaning Up

No manual cleanup is required; the `clean_database` fixture ensures each test starts with empty tables.

## Common Pitfalls

1. **Missing service‑level patch** – If a test fails with `no such table: …` or similar errors, check whether the failing code path calls a service that has its own imported `get_db_session`. Add a patch for that specific service.

2. **Foreign key constraints** – When inserting objects manually, ensure foreign‑key relationships are satisfied (e.g., a `Task` must have a valid `project_id`). Use the existing fixtures to guarantee consistency.

3. **Async session lifetime** – The `async_session` fixture yields a session that is closed after the test. Do not attempt to use the session outside the test function (e.g., in a spawned thread or a callback).

4. **Unique constraints** – The `test_id` fixture generates unique identifiers per test, but if you create objects with hard‑coded names/IDs, they may conflict with other tests. Always use `test_id` or another unique suffix.

## Example: Full Test File

See `tests/test_task_service.py` for a complete example that patches multiple services and uses the data fixtures.

## Summary

- Use `async_session` to interact with the in‑memory database.
- Rely on `patch_db_session` for global patching, but also patch service‑specific imports when needed.
- Leverage the existing data fixtures to set up common objects.
- The `clean_database` fixture guarantees isolation between tests.

By following these patterns you can write reliable, isolated database tests that run quickly and do not interfere with each other.
