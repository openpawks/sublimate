from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status

from database import engine, Base

from routers import users, projects

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="api/users/", tags=["users"])
app.include_router(projects.router, prefix="api/projects/", tags=["projects"])

@app.get("/")
def hello():
    return {"message": "Hello World"}

