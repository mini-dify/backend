from fastapi import FastAPI
from .routers import mongodb_router, qdrant_router
from .db.database import close_mongo_connection, get_database, get_qdrant_db

app = FastAPI(title="Mini-Dify Backend")

@app.on_event("startup")
def startup_db_client():
    get_database() # MongoDB
    get_qdrant_db() # Qdrant

@app.on_event("shutdown")
def shutdown_db_client():
    close_mongo_connection()

app.include_router(mongodb_router.router, prefix="/api/mongodb", tags=["MongoDB"])
app.include_router(qdrant_router.router, prefix="/api/qdrant", tags=["Qdrant"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini-Dify Backend!"}
