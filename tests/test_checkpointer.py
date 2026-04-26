import pytest
from datetime import datetime, UTC

from langgraph.checkpoint.conformance import checkpointer_test, validate

from src.services.checkpointer import (
    MyCheckpointer,
    _extract_messages_from_checkpoint,
    _get_chat_id_from_thread_id,
)
from src.db.models import CheckpointState, Message
from sqlalchemy import select


@checkpointer_test(name="MyCheckpointer")
async def my_checkpointer():
    async with MyCheckpointer() as saver:
        yield saver


@pytest.mark.asyncio
async def test_conformance():
    report = await validate(my_checkpointer)
    report.print_report()
    assert report.passed_all_base()


@pytest.mark.asyncio
async def test_checkpointer_extracts_messages_from_human_ai(async_session, test_chat):
    checkpoint = {
        "v": 1,
        "id": "test-cp-1",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {
            "messages": [
                {"type": "human", "content": "Hello from user"},
                {"type": "ai", "content": "Hello from AI"},
            ]
        },
        "channel_versions": {},
        "versions_seen": {},
    }
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }

    # Result
    await checkpointer.aput(config, checkpoint, {"source": "input", "step": 0}, {})

    rows = (
        (
            await async_session.execute(
                select(Message).where(Message.chat_id == test_chat.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2
    assert rows[0].role == "user"
    assert rows[0].content == "Hello from user"
    assert rows[1].role == "assistant"
    assert rows[1].content == "Hello from AI"


@pytest.mark.asyncio
async def test_checkpointer_extracts_tool_call_as_system(async_session, test_chat):
    checkpoint = {
        "v": 1,
        "id": "test-cp-tool",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {
            "messages": [
                {
                    "type": "ai",
                    "content": "",
                    "tool_calls": [
                        {
                            "name": "get_weather",
                            "args": {"city": "NYC"},
                            "id": "call_1",
                            "type": "tool_call",
                        }
                    ],
                },
                {"type": "human", "content": "result: 72F"},
            ]
        },
        "channel_versions": {},
        "versions_seen": {},
    }
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }

    # Result
    await checkpointer.aput(config, checkpoint, {"source": "loop", "step": 0}, {})

    rows = (
        (
            await async_session.execute(
                select(Message).where(Message.chat_id == test_chat.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2
    tool_msgs = [r for r in rows if "[Tool Call: get_weather" in r.content]
    user_msgs = [r for r in rows if r.role == "user"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].role == "assistant"
    assert len(user_msgs) == 1


@pytest.mark.asyncio
async def test_checkpointer_deduplicates_messages(async_session, test_chat):
    checkpoint = {
        "v": 1,
        "id": "test-cp-dedup",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {
            "messages": [
                {"type": "human", "content": "Hello"},
                {"type": "ai", "content": "Hi there"},
            ]
        },
        "channel_versions": {},
        "versions_seen": {},
    }
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    await checkpointer.aput(config, checkpoint, {"source": "input", "step": 0}, {})
    await checkpointer.aput(config, checkpoint, {"source": "input", "step": 1}, {})

    rows = (
        (
            await async_session.execute(
                select(Message).where(Message.chat_id == test_chat.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_checkpointer_roundtrip(async_session, test_chat):
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    cp_data = {
        "v": 1,
        "id": "roundtrip-cp-1",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {
            "messages": [{"type": "human", "content": "roundtrip test"}]
        },
        "channel_versions": {},
        "versions_seen": {},
    }
    stored = await checkpointer.aput(
        config, cp_data, {"source": "input", "step": 0}, {}
    )

    loaded = await checkpointer.aget_tuple(stored)
    assert loaded is not None
    assert loaded.checkpoint["id"] == "roundtrip-cp-1"
    assert loaded.metadata["step"] == 0
    assert loaded.metadata["source"] == "input"


@pytest.mark.asyncio
async def test_checkpointer_preserves_chat_on_delete(async_session, test_chat):
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    cp_data = {
        "v": 1,
        "id": "delete-cp-1",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {"messages": [{"type": "human", "content": "persist me"}]},
        "channel_versions": {},
        "versions_seen": {},
    }
    await checkpointer.aput(config, cp_data, {"source": "input", "step": 0}, {})

    await checkpointer.adelete_thread(str(test_chat.id))

    result = await checkpointer.aget(config)
    assert result is None

    chat_rows = (
        (
            await async_session.execute(
                select(Message).where(Message.chat_id == test_chat.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(chat_rows) == 1
    assert chat_rows[0].content == "persist me"


@pytest.mark.asyncio
async def test_checkpointer_multiple_checkpoints_for_chat(async_session, test_chat):
    checkpointer = MyCheckpointer()
    parent_config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    for i in range(3):
        cp = {
            "v": 1,
            "id": f"multi-cp-{i}",
            "ts": datetime.now(UTC).isoformat(),
            "channel_values": {"messages": [{"type": "human", "content": f"msg {i}"}]},
            "channel_versions": {},
            "versions_seen": {},
        }
        parent_config = await checkpointer.aput(
            parent_config, cp, {"source": "input", "step": i}, {}
        )

    all_tups = []
    async for tup in checkpointer.alist(
        {"configurable": {"thread_id": str(test_chat.id), "checkpoint_ns": ""}}
    ):
        all_tups.append(tup)
    assert len(all_tups) == 3

    ids = [t.checkpoint["id"] for t in all_tups]
    assert ids == [f"multi-cp-{i}" for i in range(2, -1, -1)]


@pytest.mark.asyncio
async def test_checkpointer_messages_appear_in_chat_service(async_session, test_chat):
    from src.services.chat import chat_service

    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    cp = {
        "v": 1,
        "id": "chat-svc-cp",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {
            "messages": [{"type": "human", "content": "checkpointed msg"}]
        },
        "channel_versions": {},
        "versions_seen": {},
    }
    await checkpointer.aput(config, cp, {"source": "input", "step": 0}, {})

    chat = await chat_service.get_chat_by_id(test_chat.id, async_session)
    assert chat is not None
    msgs = await chat.get_messages()
    assert any(m["content"] == "checkpointed msg" for m in msgs)


@pytest.mark.asyncio
async def test_checkpointer_idempotent_aput(async_session):
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": "9999",
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    cp = {
        "v": 1,
        "id": "idempotent-cp",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {},
        "channel_versions": {},
        "versions_seen": {},
    }

    # Results
    await checkpointer.aput(config, cp, {"source": "input", "step": 0}, {})
    await checkpointer.aput(config, cp, {"source": "input", "step": 0}, {})

    rows = (
        (
            await async_session.execute(
                select(CheckpointState).where(CheckpointState.thread_id == "9999")
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_get_chat_id_from_thread_id():
    assert _get_chat_id_from_thread_id("123") == 123
    assert _get_chat_id_from_thread_id("0") == 0
    assert _get_chat_id_from_thread_id("-1") == -1
    assert _get_chat_id_from_thread_id("abc") is None
    assert _get_chat_id_from_thread_id("") is None


@pytest.mark.asyncio
async def test_extract_messages_from_checkpoint_empty():
    assert _extract_messages_from_checkpoint({}) == []
    assert _extract_messages_from_checkpoint({"channel_values": {}}) == []
    assert _extract_messages_from_checkpoint({"channel_values": {"messages": []}}) == []


@pytest.mark.asyncio
async def test_checkpointer_non_integer_thread_id_skips_message_sync(async_session):
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": "non-integer-thread",
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    cp = {
        "v": 1,
        "id": "non-int-cp",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {
            "messages": [
                {"type": "human", "content": "should not appear in messages table"}
            ]
        },
        "channel_versions": {},
        "versions_seen": {},
    }
    await checkpointer.aput(config, cp, {"source": "input", "step": 0}, {})

    rows = (await async_session.execute(select(Message))).scalars().all()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_checkpointer_long_content_skipped(async_session, test_chat):
    checkpointer = MyCheckpointer()
    config = {
        "configurable": {
            "thread_id": str(test_chat.id),
            "checkpoint_ns": "",
            "checkpoint_id": None,
        }
    }
    long_content = "x" * 5000
    cp = {
        "v": 1,
        "id": "long-cp",
        "ts": datetime.now(UTC).isoformat(),
        "channel_values": {"messages": [{"type": "human", "content": long_content}]},
        "channel_versions": {},
        "versions_seen": {},
    }
    await checkpointer.aput(config, cp, {"source": "input", "step": 0}, {})

    rows = (
        (
            await async_session.execute(
                select(Message).where(Message.chat_id == test_chat.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 0
