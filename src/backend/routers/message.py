from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db_session


from ...services.message import message_service
from ...schemas.message import MessageCreate, MessageUpdate


router = APIRouter()


def _message_to_dict(message) -> dict:
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "content": message.content,
        "role": message.role,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.get("")
async def get_messages(
    db: Annotated[AsyncSession, Depends(get_db_session)], chat_id: int | None = None
):
    if chat_id is not None:
        messages = await message_service.get_messages_by_chat(chat_id, db)
    else:
        messages = await message_service.get_all_messages(db)
    return [_message_to_dict(m) for m in messages]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    new_message: MessageCreate, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    message = await message_service.create_message(new_message, db)
    if not message:
        raise HTTPException(status_code=400, detail="Failed to create message")
    return _message_to_dict(message)


@router.get("/{message_id}")
async def get_message(
    message_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    message = await message_service.get_message_by_id(message_id, db)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return _message_to_dict(message)


@router.patch("/{message_id}")
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    message = await message_service.update_message(message_id, message_update, db)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return _message_to_dict(message)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int, db: Annotated[AsyncSession, Depends(get_db_session)]
):
    deleted = await message_service.delete_message(message_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found")
