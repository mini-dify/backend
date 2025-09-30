from ..db.database import get_database
from ..models.item import Item
from typing import List

async def get_items() -> List[Item]:
    db = get_database()
    items_cursor = db["items"].find()
    items = await items_cursor.to_list(length=100)
    return [Item(**item) for item in items]
