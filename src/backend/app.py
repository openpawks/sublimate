from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status

from database import engine, Base

from routers import (
    users, 
    projects,
    auth,
    providers
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# NOTE: in the PLAN.md, it doesn't prefix with API... but it should be just imagine it is.
app.include_router(users.router, prefix="api/users/", tags=["users"])
app.include_router(projects.router, prefix="api/projects/", tags=["projects"])
app.include_router(auth.router, prefix="api/auth/", tags=["projects"])
app.include_router(providers.router, prefix="api/router/", tags=["projects"])

@app.get("/")
def hello():
    return {"message": "Hello World"}

