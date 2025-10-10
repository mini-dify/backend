from elasticsearch import AsyncElasticsearch
from typing import Optional

# ElasticSearch connection details
# es01 is exposed on port 9200 (from docker-compose.yml)
ES_HOSTS = ["http://localhost:9200"]

client: Optional[AsyncElasticsearch] = None

def get_es_client() -> AsyncElasticsearch:
    """
    Get or create ElasticSearch client instance (singleton pattern).

    Returns:
        AsyncElasticsearch: ElasticSearch async client instance
    """
    global client
    if client is None:
        client = AsyncElasticsearch(hosts=ES_HOSTS)
    return client

async def close_es_connection():
    """
    Close ElasticSearch client connection.
    """
    global client
    if client:
        await client.close()
        client = None
