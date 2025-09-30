from fastapi import APIRouter, status, Form, Query
from typing import List, Dict, Any
from ..services import mongodb_service

router = APIRouter()

@router.get("/databases", response_model=List[str])
async def get_database_names():
    return await mongodb_service.list_database_names()

@router.get("/collections/{db_name}", response_model=List[str])
async def get_collection_names(db_name: str):
    return await mongodb_service.list_collections(db_name=db_name)

@router.post("/create_db", status_code=status.HTTP_201_CREATED)
async def create_database(db_name: str = Form(...)):
    await mongodb_service.create_database(db_name=db_name)
    return {"message": f"Database '{db_name}' created successfully."}

@router.post("/create_collection", status_code=status.HTTP_201_CREATED)
async def create_collection(db_name: str = Form(...), collection_name: str = Form(...)):
    await mongodb_service.create_collection(db_name=db_name, collection_name=collection_name)
    return {"message": f"Collection '{collection_name}' created in database '{db_name}' successfully."}

@router.post("/data", status_code=status.HTTP_201_CREATED)
async def add_data(
    data: Dict[str, Any],
    db_name: str = Query(...),
    collection_name: str = Query(...)
):
    inserted_id = await mongodb_service.insert_data(db_name, collection_name, data)
    return {"message": "Data inserted successfully", "inserted_id": inserted_id}

@router.get("/findData", response_model=List[Dict[str, Any]])
async def find_data(
    db_name: str = Query(...),
    collection_name: str = Query(...)
):
    return await mongodb_service.find_data(db_name, collection_name)
