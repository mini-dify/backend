from fastapi import APIRouter, Depends
from typing import List
from ..models.item import Item
from ..services import item_service

router = APIRouter()

@router.get("/items", response_model=List[Item])
async def read_items():
    return await item_service.get_items()
