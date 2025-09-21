from qdrant_client import QdrantClient
from config.config import QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY
from config.constants import EMBEDDING_MODEL, EMBEDDING_DIMENSION
from openai import OpenAI

# Klient OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Klient Qdrant
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Generowanie embeddingów
def get_embeddings(text):
    result = openai_client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSION,
    )
    return result.data[0].embedding

# Wyszukiwanie embeddingów
def search_embeddings(text, collection_name):
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=get_embeddings(text),
        limit=3,
    )
    return results
