from typing import List, Dict, Any, Optional
from datetime import datetime
from ..services import mongodb_service
from ..models.assistant import CreateAssistantRequest, UpdateAssistantRequest, AssistantResponse
from ..logging_config import get_logger
import uuid

logger = get_logger(__name__)

DB_NAME = "mini_dify"
COLLECTION_NAME = "assistants"


async def create_assistant(request: CreateAssistantRequest) -> AssistantResponse:
    try:
        assistant_id = f"asst_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        assistant_data = {
            "assistant_id": assistant_id,
            "name": request.name,
            "model": request.model,
            "system_prompt": request.system_prompt,
            "temperature": request.temperature,
            "search_config": request.search_config.dict(),
            "created_at": now,
            "updated_at": now
        }

        mongo_id = await mongodb_service.insert_data(
            DB_NAME,
            COLLECTION_NAME,
            assistant_data
        )

        logger.info(f"Created assistant with ID: {assistant_id} (MongoDB ID: {mongo_id})")

        return AssistantResponse(**assistant_data)

    except Exception as e:
        logger.error(f"Failed to create assistant: {str(e)}")
        raise


async def get_assistant(assistant_id: str) -> Optional[AssistantResponse]:
    try:
        result = await mongodb_service.find_data_with_filter(
            DB_NAME,
            COLLECTION_NAME,
            {"assistant_id": assistant_id}
        )

        if not result:
            return None

        assistant_data = result[0]
        assistant_data.pop("_id", None)

        return AssistantResponse(**assistant_data)

    except Exception as e:
        logger.error(f"Failed to get assistant {assistant_id}: {str(e)}")
        raise


async def list_assistants() -> List[AssistantResponse]:
    try:
        results = await mongodb_service.find_data(DB_NAME, COLLECTION_NAME)

        assistants = []
        for doc in results:
            doc.pop("_id", None)
            assistants.append(AssistantResponse(**doc))

        logger.info(f"Retrieved {len(assistants)} assistants")
        return assistants

    except Exception as e:
        logger.error(f"Failed to list assistants: {str(e)}")
        raise


async def update_assistant(assistant_id: str, request: UpdateAssistantRequest) -> Optional[AssistantResponse]:
    try:
        # 기존 assistant 확인
        existing = await get_assistant(assistant_id)
        if not existing:
            return None

        # 업데이트할 필드만 추출
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.model is not None:
            update_data["model"] = request.model
        if request.system_prompt is not None:
            update_data["system_prompt"] = request.system_prompt
        if request.temperature is not None:
            update_data["temperature"] = request.temperature
        if request.search_config is not None:
            update_data["search_config"] = request.search_config.dict()

        update_data["updated_at"] = datetime.now().isoformat()

        modified_count = await mongodb_service.update_data(
            DB_NAME,
            COLLECTION_NAME,
            {"assistant_id": assistant_id},
            update_data
        )

        if modified_count == 0:
            logger.warning(f"No changes made to assistant {assistant_id}")

        logger.info(f"Updated assistant {assistant_id}")

        return await get_assistant(assistant_id)

    except Exception as e:
        logger.error(f"Failed to update assistant {assistant_id}: {str(e)}")
        raise


async def delete_assistant(assistant_id: str) -> bool:
    try:
        deleted_count = await mongodb_service.delete_data_with_filter(
            DB_NAME,
            COLLECTION_NAME,
            {"assistant_id": assistant_id}
        )

        if deleted_count > 0:
            logger.info(f"Deleted assistant {assistant_id}")
            return True
        else:
            logger.warning(f"Assistant {assistant_id} not found")
            return False

    except Exception as e:
        logger.error(f"Failed to delete assistant {assistant_id}: {str(e)}")
        raise
