from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from config.config import QDRANT_URL, QDRANT_API_KEY

# Klient Qdrant
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def create_collection_if_not_exists(collection_name: str, vector_size: int, distance: str = "Cosine"):
    """
    Tworzy kolekcję w Qdrant, jeśli jeszcze nie istnieje.
    """
    if collection_name not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config={"default": {"size": vector_size, "distance": distance}}
        )

def insert_embedding(collection_name: str, point_id: str, vector: list[float], payload: dict):
    """
    Wstawia embedding do Qdrant.
    """
    client.upsert(
        collection_name=collection_name,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)]
    )

def search_embeddings(collection_name: str, query_vector: list[float], top_k: int = 5, filters: dict = None):
    """
    Wyszukuje najbliższe embeddingi w kolekcji.
    """
    query_filter = None
    if filters:
        # prosty przykład: {"field": "type", "value": "dynamic"}
        query_filter = Filter(
            must=[FieldCondition(key=filters["field"], match=MatchValue(value=filters["value"]))]
        )

    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter
    )
    return results
