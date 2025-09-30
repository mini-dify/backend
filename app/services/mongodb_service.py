from ..db.database import get_client
from typing import List

async def list_database_names() -> List[str]:
    client = get_client()
    return await client.list_database_names()
