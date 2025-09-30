from fastapi import APIRouter
from typing import List
from ..services import mongodb_service

router = APIRouter()

@router.get("/databases", response_model=List[str])
async def get_database_names():
    return await mongodb_service.list_database_names()
