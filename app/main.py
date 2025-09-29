from fastapi import FastAPI
from .routers import chat

app = FastAPI(title="Mini-Dify Backend")

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini-Dify Backend!"}
