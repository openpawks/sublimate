from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db_session

from ...services.chat import chat_service

router = APIRouter()


def _chat_to_dict(chat) -> dict:
    db = chat.db_object
    return {
        "id": db.id,
        "task_id": db.task_id,
        "created_at": db.created_at.isoformat() if db.created_at else None,
    }


@router.get("")
async def get_chats(
    db: Annotated[AsyncSession, Depends(get_db_session)], task_id: int | None = None
):
    if task_id is not None:
        chats = await chat_service.get_chats_by_task(task_id, db)
    else:
        chats = await chat_service.get_all_chats(db)
    return [_chat_to_dict(c) for c in chats]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_chat(
    task_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    chat = await chat_service.create_chat(task_id, db)
    if not chat:
        raise HTTPException(status_code=400, detail="Failed to create chat")
    return _chat_to_dict(chat)


@router.get("/{chat_id}")
async def get_chat(chat_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]):
    chat = await chat_service.get_chat_by_id(chat_id, db)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_to_dict(chat)


@router.patch("/{chat_id}")
async def update_chat(
    chat_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    task_id: int | None = None,
):
    chat = await chat_service.update_chat(chat_id, db, task_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_to_dict(chat)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    deleted = await chat_service.delete_chat(chat_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
