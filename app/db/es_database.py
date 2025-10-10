from elasticsearch import AsyncElasticsearch
from typing import Optional

# ElasticSearch connection details
# Connect to all 3 Elasticsearch nodes for high availability
ES_HOSTS = [
    "http://es01:9200",
    "http://es02:9200",
    "http://es03:9200"
]

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