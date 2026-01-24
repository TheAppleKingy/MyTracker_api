from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from dishka.integrations.fastapi import setup_dishka
from sqlalchemy.orm import registry, relationship, column_property

from src.domain.entities import User, Task
from src.domain.exc import HandledError
from src.interfaces.http import *
from src.infra.db.tables import tasks, users
from src.container import container
from src.logger import logger


def map_tables():
    mapper_registry = registry()
    mapper_registry.map_imperatively(User, users, properties={
        "tasks": relationship(Task, lazy='raise', cascade="all, delete-orphan", passive_deletes=True)
    })
    mapper_registry.map_imperatively(Task, tasks, properties={
        "_deadline": column_property(tasks.c.deadline),
        "subtasks": relationship(
            Task,
            back_populates="parent",
            lazy="raise",
            cascade="all, delete-orphan",
            passive_deletes=True,
            remote_side=[tasks.c.parent_id],
        ),
        "parent": relationship(Task, back_populates="subtasks", lazy='raise', uselist=False, remote_side=[tasks.c.id])
    })
    mapper_registry.configure()


@asynccontextmanager
async def lifespan(app: FastAPI):
    map_tables()
    setup_routers(app)
    logger.info("Tracker backend is ready. Starting...")
    yield
    logger.info("Tracker backend shitdown")
    await container.close()


app = FastAPI(lifespan=lifespan)
setup_dishka(container, app)


@app.middleware("http")
async def handle_auth(r: Request, call_next):
    try:
        return await call_next(r)
    except HandledError as e:
        return JSONResponse({"detail": str(e)}, e.status)


def setup_routers(app: FastAPI):
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(task_router)
    api_router.include_router(auth_router)
    app.include_router(api_router)
