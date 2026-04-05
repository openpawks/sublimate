from typing import Annotated

from fastapi import APIRouter, status, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db


router = APIRouter()

