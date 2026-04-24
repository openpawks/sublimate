from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from ..db.database import engine, Base

from .routers import project, task, agent, chat, message, provider


# CRITICAL: NoCacheStaticFiles disables all caching for rapid prototyping.
# Without this, browsers aggressively cache CSS/JS, forcing hard-refresh
# on every change. Remove or switch to StaticFiles for production.
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


HERE = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(HERE / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/static", NoCacheStaticFiles(directory=str(HERE / "static")), name="static")

app.include_router(project.router, prefix="/api/v0/projects", tags=["projects"])
app.include_router(task.router, prefix="/api/v0/tasks", tags=["tasks"])
app.include_router(agent.router, prefix="/api/v0/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/v0/chats", tags=["chats"])
app.include_router(message.router, prefix="/api/v0/messages", tags=["messages"])
app.include_router(provider.router, prefix="/api/v0/providers", tags=["providers"])


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
