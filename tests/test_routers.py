import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.db.database import Base


@pytest_asyncio.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def router_engine():
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


@pytest_asyncio.fixture
async def router_session(router_engine):
    AsyncSessionLocal = async_sessionmaker(
        router_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def clean_db(router_session):
    await router_session.execute(text("PRAGMA foreign_keys = OFF"))
    tables = [
        "messages",
        "senders",
        "task_to_agent",
        "agents",
        "providers",
        "chats",
        "tasks",
        "projects",
        "users",
    ]
    for table in tables:
        await router_session.execute(text(f"DELETE FROM {table}"))
    await router_session.execute(text("PRAGMA foreign_keys = ON"))
    await router_session.commit()


@pytest_asyncio.fixture
async def client(router_session):
    async def mock_get_db_session():
        return router_session

    import src.services.project
    import src.services.agent
    import src.services.chat
    import src.services.message
    import src.services.provider
    import src.services.task

    for mod in [
        src.services.project,
        src.services.agent,
        src.services.chat,
        src.services.message,
        src.services.provider,
        src.services.task,
    ]:
        mod.get_db_session = mock_get_db_session

    from src.backend.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestProjectRouter:
    async def test_list_empty(self, client):
        resp = await client.get("/api/v0/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_and_get(self, client):
        resp = await client.post(
            "/api/v0/projects",
            json={
                "name": "Test Project",
                "user_id": 1,
                "root_dir": "/tmp/test_project.git",
                "settings_yaml": "test: settings",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Project"
        assert data["user_id"] == 1
        assert "id" in data

        get = await client.get(f"/api/v0/projects/{data['id']}")
        assert get.status_code == 200
        assert get.json()["name"] == "Test Project"

    async def test_get_not_found(self, client):
        assert (await client.get("/api/v0/projects/9999")).status_code == 404

    async def test_update(self, client):
        create = (
            await client.post(
                "/api/v0/projects",
                json={"name": "Before", "user_id": 1, "root_dir": "/tmp/before.git"},
            )
        ).json()

        resp = await client.patch(
            f"/api/v0/projects/{create['id']}", json={"name": "After"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "After"

    async def test_update_not_found(self, client):
        assert (
            await client.patch("/api/v0/projects/9999", json={"name": "Nope"})
        ).status_code == 404

    async def test_delete(self, client):
        create = (
            await client.post(
                "/api/v0/projects",
                json={"name": "To Delete", "user_id": 1, "root_dir": "/tmp/delete.git"},
            )
        ).json()

        assert (
            await client.delete(f"/api/v0/projects/{create['id']}")
        ).status_code == 204
        assert (await client.get(f"/api/v0/projects/{create['id']}")).status_code == 404

    async def test_delete_not_found(self, client):
        assert (await client.delete("/api/v0/projects/9999")).status_code == 404

    async def test_filter_by_user(self, client):
        await client.post(
            "/api/v0/projects",
            json={"name": "User 1", "user_id": 1, "root_dir": "/tmp/u1.git"},
        )
        await client.post(
            "/api/v0/projects",
            json={"name": "User 2", "user_id": 2, "root_dir": "/tmp/u2.git"},
        )

        resp = await client.get("/api/v0/projects?user_id=1")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestProviderRouter:
    async def test_list_empty(self, client):
        assert (await client.get("/api/v0/providers")).json() == []

    async def test_create_and_get(self, client):
        resp = await client.post(
            "/api/v0/providers",
            json={"id": "my-provider", "name": "My Provider", "api_key": "key-123"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "My Provider"

        get = await client.get("/api/v0/providers/my-provider")
        assert get.status_code == 200
        assert get.json()["name"] == "My Provider"

    async def test_get_not_found(self, client):
        assert (await client.get("/api/v0/providers/nonexistent")).status_code == 404

    async def test_update(self, client):
        await client.post(
            "/api/v0/providers",
            json={"id": "upd-p", "name": "Before", "api_key": "old"},
        )
        resp = await client.patch("/api/v0/providers/upd-p", json={"name": "After"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "After"

    async def test_delete(self, client):
        await client.post(
            "/api/v0/providers",
            json={"id": "del-p", "name": "To Delete", "api_key": "del"},
        )
        assert (await client.delete("/api/v0/providers/del-p")).status_code == 204
        assert (await client.get("/api/v0/providers/del-p")).status_code == 404

    async def test_delete_not_found(self, client):
        assert (await client.delete("/api/v0/providers/nonexistent")).status_code == 404


class TestAgentRouter:
    async def _setup(self, client):
        proj = (
            await client.post(
                "/api/v0/projects",
                json={"name": "Agent Proj", "user_id": 1, "root_dir": "/tmp/ap.git"},
            )
        ).json()
        prov = (
            await client.post(
                "/api/v0/providers",
                json={"id": "agent-prov", "name": "Agent Prov", "api_key": "ak"},
            )
        ).json()
        return proj, prov

    async def test_list_empty(self, client):
        assert (await client.get("/api/v0/agents")).json() == []

    async def test_create_and_get(self, client):
        proj, prov = await self._setup(client)
        resp = await client.post(
            "/api/v0/agents",
            json={
                "name": "Test Agent",
                "project_id": proj["id"],
                "provider_id": prov["id"],
                "model_name": "gpt-4",
                "prompt": "You are a test agent",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Agent"

        get = await client.get(f"/api/v0/agents/{resp.json()['id']}")
        assert get.status_code == 200

    async def test_get_not_found(self, client):
        assert (await client.get("/api/v0/agents/9999")).status_code == 404

    async def test_update(self, client):
        proj, prov = await self._setup(client)
        agent = (
            await client.post(
                "/api/v0/agents",
                json={
                    "name": "Before",
                    "project_id": proj["id"],
                    "provider_id": prov["id"],
                    "model_name": "old",
                    "prompt": "Old prompt",
                },
            )
        ).json()

        resp = await client.patch(
            f"/api/v0/agents/{agent['id']}",
            json={"name": "After", "model_name": "new"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "After"
        assert resp.json()["model_name"] == "new"

    async def test_delete(self, client):
        proj, prov = await self._setup(client)
        agent = (
            await client.post(
                "/api/v0/agents",
                json={
                    "name": "To Delete",
                    "project_id": proj["id"],
                    "provider_id": prov["id"],
                    "model_name": "del",
                    "prompt": "Delete me",
                },
            )
        ).json()

        assert (await client.delete(f"/api/v0/agents/{agent['id']}")).status_code == 204
        assert (await client.get(f"/api/v0/agents/{agent['id']}")).status_code == 404

    async def test_filter_by_project(self, client):
        proj, prov = await self._setup(client)
        await client.post(
            "/api/v0/agents",
            json={
                "name": "Agent A",
                "project_id": proj["id"],
                "provider_id": prov["id"],
                "model_name": "m1",
                "prompt": "A",
            },
        )

        resp = await client.get(f"/api/v0/agents?project_id={proj['id']}")
        assert resp.status_code == 200
        assert any(a["name"] == "Agent A" for a in resp.json())


class TestTaskRouter:
    async def _setup(self, client):
        proj = (
            await client.post(
                "/api/v0/projects",
                json={"name": "Task Proj", "user_id": 1, "root_dir": "/tmp/tp.git"},
            )
        ).json()
        return proj

    async def test_list_empty(self, client):
        assert (await client.get("/api/v0/tasks")).json() == []

    async def test_create_and_get(self, client):
        proj = await self._setup(client)
        resp = await client.post(
            "/api/v0/tasks",
            json={
                "name": "my-task",
                "project_id": proj["id"],
                "root_dir": "/tmp/my_task",
                "goal": "Do something",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "my-task"
        assert data["project_id"] == proj["id"]

        get = await client.get(f"/api/v0/tasks/{data['id']}")
        assert get.status_code == 200
        assert get.json()["name"] == "my-task"

    async def test_get_not_found(self, client):
        assert (await client.get("/api/v0/tasks/9999")).status_code == 404

    async def test_create_invalid_name(self, client):
        proj = await self._setup(client)
        resp = await client.post(
            "/api/v0/tasks",
            json={
                "name": "invalid name with spaces",
                "project_id": proj["id"],
                "root_dir": "/tmp/bad",
                "goal": "Test",
            },
        )
        assert resp.status_code == 404

    async def test_update(self, client):
        proj = await self._setup(client)
        task = (
            await client.post(
                "/api/v0/tasks",
                json={
                    "name": "update-task",
                    "project_id": proj["id"],
                    "root_dir": "/tmp/update",
                    "goal": "Original goal",
                },
            )
        ).json()

        resp = await client.patch(
            f"/api/v0/tasks/{task['id']}",
            json={"name": "updated-name", "todos": "New todos"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "updated-name"
        assert resp.json()["todos"] == "New todos"

    async def test_delete(self, client):
        proj = await self._setup(client)
        task = (
            await client.post(
                "/api/v0/tasks",
                json={
                    "name": "delete-task",
                    "project_id": proj["id"],
                    "root_dir": "/tmp/delete",
                    "goal": "Delete me",
                },
            )
        ).json()

        assert (await client.delete(f"/api/v0/tasks/{task['id']}")).status_code == 204
        assert (await client.get(f"/api/v0/tasks/{task['id']}")).status_code == 404

    async def test_filter_by_project(self, client):
        proj = await self._setup(client)
        await client.post(
            "/api/v0/tasks",
            json={
                "name": "task-1",
                "project_id": proj["id"],
                "root_dir": "/tmp/t1",
                "goal": "G1",
            },
        )

        resp = await client.get(f"/api/v0/tasks?project_id={proj['id']}")
        assert resp.status_code == 200
        assert any(t["name"] == "task-1" for t in resp.json())


class TestChatRouter:
    async def _setup(self, client):
        proj = (
            await client.post(
                "/api/v0/projects",
                json={"name": "Chat Proj", "user_id": 1, "root_dir": "/tmp/cp.git"},
            )
        ).json()
        task = (
            await client.post(
                "/api/v0/tasks",
                json={
                    "name": "chat-task",
                    "project_id": proj["id"],
                    "root_dir": "/tmp/ct",
                    "goal": "Chat goal",
                },
            )
        ).json()
        return proj, task

    async def test_list_empty(self, client):
        assert (await client.get("/api/v0/chats")).json() == []

    async def test_create_and_get(self, client):
        _, task = await self._setup(client)
        resp = await client.post("/api/v0/chats", params={"task_id": task["id"]})
        assert resp.status_code == 201
        assert resp.json()["task_id"] == task["id"]

        get = await client.get(f"/api/v0/chats/{resp.json()['id']}")
        assert get.status_code == 200

    async def test_get_not_found(self, client):
        assert (await client.get("/api/v0/chats/9999")).status_code == 404

    async def test_delete(self, client):
        _, task = await self._setup(client)
        chat = (
            await client.post("/api/v0/chats", params={"task_id": task["id"]})
        ).json()

        assert (await client.delete(f"/api/v0/chats/{chat['id']}")).status_code == 204
        assert (await client.get(f"/api/v0/chats/{chat['id']}")).status_code == 404

    async def test_delete_not_found(self, client):
        assert (await client.delete("/api/v0/chats/9999")).status_code == 404


class TestMessageRouter:
    async def _setup(self, client):
        proj = (
            await client.post(
                "/api/v0/projects",
                json={"name": "Msg Proj", "user_id": 1, "root_dir": "/tmp/mp.git"},
            )
        ).json()
        task = (
            await client.post(
                "/api/v0/tasks",
                json={
                    "name": "msg-task",
                    "project_id": proj["id"],
                    "root_dir": "/tmp/mt",
                    "goal": "Msg goal",
                },
            )
        ).json()
        chat = (
            await client.post("/api/v0/chats", params={"task_id": task["id"]})
        ).json()
        return proj, task, chat

    async def test_list_empty(self, client):
        assert (await client.get("/api/v0/messages")).json() == []

    async def test_create_and_get(self, client):
        _, _, chat = await self._setup(client)
        resp = await client.post(
            "/api/v0/messages",
            json={"chat_id": chat["id"], "content": "Hello!", "role": "user"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "Hello!"
        assert data["role"] == "user"
        assert data["chat_id"] == chat["id"]

        get = await client.get(f"/api/v0/messages/{data['id']}")
        assert get.status_code == 200
        assert get.json()["content"] == "Hello!"

    async def test_get_not_found(self, client):
        assert (await client.get("/api/v0/messages/9999")).status_code == 404

    async def test_update(self, client):
        _, _, chat = await self._setup(client)
        msg = (
            await client.post(
                "/api/v0/messages",
                json={"chat_id": chat["id"], "content": "Original", "role": "user"},
            )
        ).json()

        resp = await client.patch(
            f"/api/v0/messages/{msg['id']}", json={"content": "Updated"}
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "Updated"

    async def test_delete(self, client):
        _, _, chat = await self._setup(client)
        msg = (
            await client.post(
                "/api/v0/messages",
                json={"chat_id": chat["id"], "content": "Delete me", "role": "user"},
            )
        ).json()

        assert (await client.delete(f"/api/v0/messages/{msg['id']}")).status_code == 204
        assert (await client.get(f"/api/v0/messages/{msg['id']}")).status_code == 404
