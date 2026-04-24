# Streaming & Task Execution

## Problem

There's no way for a client to observe agent execution live. `repeat_until_complete()` blocks until the entire agent conversation is done, then saves everything to the DB. The gap is between:
- `WorkerAgent.ainvoke()` (Langchain call) → `repeat_until_complete()` loop → DB persistence
- No events are emitted during execution

The streaming `WS /ws/tasks/{task_id}/chat` endpoint is already planned but unimplemented.

## Architecture

```
Client (WS)           FastAPI                WorkerAgent.astream()        Langchain
   │                     │                         │                        │
   ├─connect────┬───────►│                         │                        │
   │◄─accepted──┘        │                         │                        │
   │                     │  get BaseTask by ID     │                        │
   │                     ├─repeat_until_complete()─►                        │
   │                     │  (with event_emitter)   │                        │
   │                     │                         ├──astream_events()─────►│
   │◄─{"type":"token"}───┤◄──emit(event)────────────┤◄──on_chat_model_stream│
   │◄─{"type":"tool_start"}                         │◄──on_tool_start       │
   │◄─{"type":"tool_end"}                           │◄──on_tool_end         │
   │◄─{"type":"message_done"}                       │◄──on_chain_end        │
   │                     │  saves full msg to DB    │                        │
```

## Event Wire Format

All events are JSON with `{ "type": str, "data": {} }`.

| type | data fields | source Langchain event |
|------|-------------|----------------------|
| `token` | `{ content: str }` | `on_chat_model_stream` |
| `tool_start` | `{ name: str, input: dict }` | `on_tool_start` |
| `tool_end` | `{ name: str, output: str }` | `on_tool_end` |
| `message_done` | `{ agent_name: str, content: str }` | synthesized after full response |
| `iteration_start` | `{ iteration: int, agent_name: str }` | synthesized |
| `iteration_done` | `{ iteration: int, agent_name: str }` | synthesized |
| `task_done` | `{}` | synthesized after loop ends |
| `error` | `{ message: str }` | synthesized |

## API Endpoints

### `POST /api/v0/tasks/{task_id}/execute`

Fire-and-forget execution. Runs `repeat_until_complete()` synchronously. Returns when done.

### `WS /ws/v0/tasks/{task_id}/chat`

Bidirectional WebSocket. On connect:
1. If task not running → starts execution and streams events
2. If task already running → subscribes to events (subscriber pattern not yet implemented — initial impl: WS triggers execution)
3. Client can send JSON messages `{ "role": "user", "content": "..." }` which get appended to chat and picked up on next iteration

## Execution Lock

`BaseTask` has an `_executing: bool` flag to prevent concurrent execution:

```python
# in BaseTask
self._executing: bool = False

async def repeat_until_complete(self, db, max_iterations=100, event_emitter=None):
    if self._executing:
        raise RuntimeError("Task is already executing")
    self._executing = True
    try:
        # ... existing logic ...
    finally:
        self._executing = False
```

```
Client A ──WS────► repeat_until_complete() starts ──► _executing = True
Client B ──POST──► repeat_until_complete() rejected ──► 409 Conflict
```

## File Changes

| File | Change |
|------|--------|
| `src/schemas/stream.py` | **NEW** — event type Pydantic models |
| `src/orchestration/agent.py` | Add `WorkerAgent.astream()` — wraps `agent.astream_events()` |
| `src/orchestration/task.py` | Add `event_emitter` param to `repeat_until_complete()`; add `_executing` lock |
| `src/backend/routers/ws.py` | **NEW** — WebSocket endpoint |
| `src/backend/routers/task.py` | Add `POST /{task_id}/execute` |
| `src/backend/app.py` | Register WS router |

## Sequence: Full WS Flow

```
Client                    FastAPI                          WorkerAgent           DB
  │                         │                                │                   │
  ├─ WS connect ───────────►│                                │                   │
  │◄─ accept ──────────────┤                                │                   │
  │                         ├── get BaseTask ───────────────►│                   │
  │                         │  init_repo(), init_agent()      │                   │
  │                         │                                │                   │
  │                         ├── repeat_until_complete()─────►│                   │
  │                         │  [iteration loop]              │                   │
  │◄─ iteration_start ─────┤                                │                   │
  │◄─ token ───────────────┤◄── astream_events() ───────────┤                   │
  │◄─ tool_start ──────────┤                                │                   │
  │◄─ tool_end ────────────┤                                │                   │
  │◄─ message_done ────────┤                                ├── add_message()──►│
  │                         │                                │                   │
  │  [user sends message]   │                                │                   │
  ├─ {role:"user",...} ────►│  add_message() ───────────────►├── add_message()──►│
  │                         │  [next iteration picks it up]  │                   │
  │                         │                                │                   │
  │◄─ task_done ───────────┤                                │                   │
  │◄─ close ──────────────┤                                │                   │
```

### Notes on agent tool use during streaming

The simple ainvoke path hides tool calls from the caller — it only returns the final `AIMessage`. The `astream_events()` approach exposes all intermediate steps. The event emitter sends these as `tool_start` / `tool_end` events so the frontend can render tool invocations inline (e.g. showing the agent running a command, reading a file, etc.).

## Agent Loop (Token Accumulation)

Even though we stream tokens live, we accumulate them and save the complete message to the DB after each agent invocation:

```python
full_content = ""
async for event in agent.astream(messages):
    await event_emitter(event)
    if event["type"] == "token":
        full_content += event["data"]["content"]

# Save complete message (not partial tokens) to DB
await self.chat.add_message(db=db, role="assistant", content=full_content, ...)
```

This means:
- Client sees typewriter effect via `token` events
- DB has clean complete messages (no partial/concatenated entries)
- If client disconnects mid-stream, the last complete message is still saved

### `WorkerAgent.astream()` implementation

```python
async def astream(self, messages: list):
    """Yields streaming events dicts from agent execution."""
    if not self.agent:
        raise ValueError("Agent not initialized")
    inp = {"messages": [{"role": "system", "content": self.prompt}, *messages]}
    async for event in self.agent.astream_events(inp, version="v2"):
        etype = event["event"]
        if etype == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                yield {"type": "token", "data": {"content": chunk.content}}
        elif etype == "on_tool_start":
            yield {"type": "tool_start", "data": {"name": event["name"], "input": event["data"].get("input")}}
        elif etype == "on_tool_end":
            yield {"type": "tool_end", "data": {"name": event["name"], "output": str(event["data"].get("output"))}}
```

### `BaseTask.repeat_until_complete()` — streaming path

```python
async def repeat_until_complete(self, db, max_iterations=100, event_emitter=None):
    if self._executing:
        raise RuntimeError("Task is already executing")
    self._executing = True
    try:
        if not self.repo:
            self.init_all()
        self.repeating_until_complete = True
        iteration = 0

        while self.repeating_until_complete and self.open and iteration < max_iterations:
            agent = self.get_active_agent()
            if not agent.agent:
                self.init_agent(agent)

            if event_emitter:
                await event_emitter({"type": "iteration_start",
                                     "data": {"iteration": iteration, "agent_name": agent.name}})

            full_content = ""
            if event_emitter:
                async for event in agent.astream(self.chat.get_messages()):
                    await event_emitter(event)
                    if event["type"] == "token":
                        full_content += event["data"]["content"]
            else:
                output = await self.invoke_agent(agent, self.chat.get_messages())
                full_content = output.content

            await self.chat.add_message(db=db, role="assistant", content=full_content, username=agent.name)

            if event_emitter:
                await event_emitter({"type": "message_done",
                                     "data": {"agent_name": agent.name, "content": full_content}})

            iteration += 1
            if iteration >= max_iterations:
                self.repeating_until_complete = False
                await self.chat.add_message(
                    db=db, role="system",
                    content=f"Stopped after {max_iterations} iterations (safety limit).",
                    username="system",
                )
            if self.repo and self.open:
                try:
                    self.commit_changes("Auto commit on task completion")
                except Exception as e:
                    print(f"Auto commit failed: {e}")
    finally:
        self._executing = False
```

### WebSocket router

```python
router = APIRouter()

@router.websocket("/ws/v0/tasks/{task_id}/chat")
async def task_chat_ws(websocket: WebSocket, task_id: int):
    await websocket.accept()

    task = registry.task_service.get_base_task_by_id(task_id)
    if not task:
        await websocket.send_json({"type": "error", "data": {"message": "Task not found"}})
        await websocket.close()
        return

    async def emit(event):
        await websocket.send_json(event)

    async with AsyncSessionLocal() as db:
        try:
            await task.repeat_until_complete(db, event_emitter=emit)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        finally:
            await websocket.close()
```

### POST execute endpoint

```python
@router.post("/{task_id}/execute")
async def execute_task(task_id: int):
    task = registry.task_service.get_base_task_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    async with AsyncSessionLocal() as db:
        await task.repeat_until_complete(db)
    return {"status": "completed", "task_id": task_id}
```

## Implementation Order

1. Add `_executing` lock to `BaseTask`
2. Add `WorkerAgent.astream()` method
3. Modify `repeat_until_complete()` with `event_emitter` parameter
4. Create `src/schemas/stream.py` (optional — can use inline dicts)
5. Create `src/backend/routers/ws.py`
6. Add `POST /{task_id}/execute` to task router
7. Register WS router in `app.py`
