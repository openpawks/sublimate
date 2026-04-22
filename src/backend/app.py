from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from ..db.database import engine, Base

from .routers import project, task, agent, chat, message, provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(project.router, prefix="/api/v0/projects", tags=["projects"])
app.include_router(task.router, prefix="/api/v0/tasks", tags=["tasks"])
app.include_router(agent.router, prefix="/api/v0/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/v0/chats", tags=["chats"])
app.include_router(message.router, prefix="/api/v0/messages", tags=["messages"])
app.include_router(provider.router, prefix="/api/v0/providers", tags=["providers"])


@app.get("/")
def hello():
    return {"message": "Hello World"}


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
