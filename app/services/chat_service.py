from .. import schemas


def get_chat_response(request: schemas.ChatRequest) -> schemas.ChatResponse:
    mock_reply = f"You said: {request.message}"
    return schemas.ChatResponse(reply=mock_reply)
