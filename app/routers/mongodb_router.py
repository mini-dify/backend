from fastapi import APIRouter, status, Form, Query, Body
from typing import List, Dict, Any, Optional
from ..services import mongodb_service
from ..models.mongodb import UpdateDataRequest, DeleteDataWithFilterRequest
import json

router = APIRouter(
    prefix="/mongodb",
    tags=["mongodb"],
)
@router.get(
    "/databases",
    response_model=List[str],
    summary="데이터베이스 목록 조회",
    description="MongoDB 서버에 존재하는 모든 데이터베이스의 이름을 조회합니다."
)
async def get_database_names():
    return await mongodb_service.list_database_names()

@router.get(
    "/collections/{db_name}",
    response_model=List[str],
    summary="컬렉션 목록 조회",
    description="특정 데이터베이스에 존재하는 모든 컬렉션의 이름을 조회합니다."
)
async def get_collection_names(db_name: str):
    return await mongodb_service.list_collections(db_name=db_name)

@router.post(
    "/create_db",
    status_code=status.HTTP_201_CREATED,
    summary="데이터베이스 생성",
    description="지정된 이름의 데이터베이스를 생성합니다. (내부에 임시 컬렉션 생성)"
)
async def create_database(db_name: str = Form(...)):
    await mongodb_service.create_database(db_name=db_name)
    return {"message": f"Database '{db_name}' created successfully."}

@router.post(
    "/create_collection",
    status_code=status.HTTP_201_CREATED,
    summary="컬렉션 생성",
    description="지정된 데이터베이스 내에 새로운 컬렉션을 생성합니다."
)
async def create_collection(db_name: str = Form(...), collection_name: str = Form(...)):
    await mongodb_service.create_collection(db_name=db_name, collection_name=collection_name)
    return {"message": f"Collection '{collection_name}' created in database '{db_name}' successfully."}

@router.post(
    "/data",
    status_code=status.HTTP_201_CREATED,
    summary="데이터 저장",
    description="지정된 데이터베이스의 컬렉션에 새로운 문서를 저장합니다."
)
async def add_data(
    db_name: str = Query(...),
    collection_name: str = Query(...),
    data: Dict[str, Any] = Body(...)
):
    inserted_id = await mongodb_service.insert_data(db_name, collection_name, data)
    return {"message": "Data inserted successfully", "inserted_id": inserted_id}

@router.get(
    "/findData",
    response_model=List[Dict[str, Any]],
    summary="데이터 조회 (모든 문서)",
    description="지정된 데이터베이스의 컬렉션에 있는 모든 문서를 조회합니다. (최대 100개)"
)
async def find_data(
    db_name: str = Query(...),
    collection_name: str = Query(...)
):
    return await mongodb_service.find_data(db_name, collection_name)

@router.post(
    "/findDataWithFilter",
    response_model=List[Dict[str, Any]],
    summary="데이터 조회 (필터링)",
    description="지정된 데이터베이스의 컬렉션에서 필터 조건에 맞는 문서를 조회합니다. (최대 100개)"
)
async def find_data_with_filter(
    db_name: str = Query(...),
    collection_name: str = Query(...),
    query_filter: Dict[str, Any] = Body(..., description="JSON 형식의 쿼리 필터 (예: {\"name\": \"test\"})")
):
    return await mongodb_service.find_data_with_filter(db_name, collection_name, query_filter)

@router.get(
    "/findDataById/{db_name}/{collection_name}/{doc_id}",
    response_model=Optional[Dict[str, Any]],
    summary="단일 데이터 조회 (ID)",
    description="지정된 데이터베이스의 컬렉션에서 특정 ID를 가진 문서를 조회합니다."
)
async def find_data_by_id(
    db_name: str,
    collection_name: str,
    doc_id: str
):
    return await mongodb_service.find_data_by_id(db_name, collection_name, doc_id)

@router.put(
    "/updateData",
    summary="데이터 업데이트",
    description="지정된 데이터베이스의 컬렉션에서 필터 조건에 맞는 문서를 업데이트합니다."
)
async def update_data(
    db_name: str = Query(...),
    collection_name: str = Query(...),
    request: UpdateDataRequest = Body(...)
):
    modified_count = await mongodb_service.update_data(
        db_name, collection_name, request.query_filter, request.update_data, request.upsert, request.multi
    )
    return {"message": f"{modified_count} document(s) updated successfully."}

@router.delete(
    "/deleteDataWithFilter",
    summary="데이터 삭제 (필터링)",
    description="지정된 데이터베이스의 컬렉션에서 필터 조건에 맞는 문서를 삭제합니다."
)
async def delete_data_with_filter(
    db_name: str = Query(...),
    collection_name: str = Query(...),
    request: DeleteDataWithFilterRequest = Body(...)
):
    deleted_count = await mongodb_service.delete_data_with_filter(db_name, collection_name, request.query_filter)
    return {"message": f"{deleted_count} document(s) deleted successfully."}

@router.delete(
    "/delete_db",
    status_code=status.HTTP_200_OK,
    summary="데이터베이스 삭제",
    description="지정된 데이터베이스를 삭제합니다."
)
async def delete_db(db_name: str = Query(...)):
    await mongodb_service.delete_database(db_name=db_name)
    return {"message": f"Database '{db_name}' deleted successfully."}

@router.delete(
    "/delete_collection",
    status_code=status.HTTP_200_OK,
    summary="컬렉션 삭제",
    description="지정된 데이터베이스 내의 컬렉션을 삭제합니다."
)
async def delete_collection(
    db_name: str = Query(...),
    collection_name: str = Query(...)
):
    await mongodb_service.delete_collection(db_name=db_name, collection_name=collection_name)
    return {"message": f"Collection '{collection_name}' deleted from database '{db_name}' successfully."}