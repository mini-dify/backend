from fastapi import FastAPI, Depends
from .routers import mongodb_router, qdrant_router, es_router, developCellApi_embedding, developCellApi_llm, document_router, search_router
from .db.database import close_mongo_connection, get_database, get_qdrant_db
from .security import check_auth
from .logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Mini-Dify Backend",
    dependencies=[Depends(check_auth)]
)

@app.on_event("startup")
def startup_db_client():
    logger.info("Starting up application...")
    get_database()
    get_qdrant_db()
    logger.info("Database connections initialized")

@app.on_event("shutdown")
def shutdown_db_client():
    logger.info("Shutting down application...")
    close_mongo_connection()
    logger.info("Application shutdown complete")


app.include_router(mongodb_router.router, prefix="/mongodb", tags=["MongoDB"])
app.include_router(qdrant_router.router, prefix="/qdrant", tags=["Qdrant"])
app.include_router(es_router.router, prefix="/elasticsearch", tags=["Elasticsearch"])


app.include_router(developCellApi_embedding.router, prefix="/developCell", tags=["DevelopCell-Embedding"])
app.include_router(developCellApi_llm.router, prefix="/developCell", tags=["DevelopCell-LLM"])
app.include_router(document_router.router, prefix="/document", tags=["Document"])
app.include_router(search_router.router, prefix="/search", tags=["Search"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini-Dify Backend!"}
