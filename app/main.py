from fastapi import FastAPI, Depends
from .routers import mongodb_router, qdrant_router, developCellApi_embedding, developCellApi_llm
from .db.database import close_mongo_connection, get_database, get_qdrant_db
from .security import check_auth

app = FastAPI(
    title="Mini-Dify Backend",
    dependencies=[Depends(check_auth)]
)

@app.on_event("startup")
def startup_db_client():
    get_database()
    get_qdrant_db()

@app.on_event("shutdown")
def shutdown_db_client():
    close_mongo_connection()


app.include_router(mongodb_router.router, prefix="/mongodb", tags=["MongoDB"])
app.include_router(qdrant_router.router, prefix="/qdrant", tags=["Qdrant"])


app.include_router(developCellApi_embedding.router, prefix="/developCell", tags=["DevelopCell-Embedding"])
app.include_router(developCellApi_llm.router, prefix="/developCell", tags=["DevelopCell-LLM"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini-Dify Backend!"}
