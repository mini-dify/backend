from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    description: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            str: lambda v: str(v)
        }
