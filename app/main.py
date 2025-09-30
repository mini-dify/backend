from fastapi import FastAPI
from .routers import chat, item_router
from .db.database import close_mongo_connection, get_database

app = FastAPI(title="Mini-Dify Backend")

@app.on_event("startup")
def startup_db_client():
    get_database()

@app.on_event("shutdown")
def shutdown_db_client():
    close_mongo_connection()

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(item_router.router, prefix="/api/v1", tags=["Items"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini-Dify Backend!"}
