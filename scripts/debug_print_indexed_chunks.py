import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.vector_storage import VectorStorage
from app.services.embedding_service import EmbeddingService

embedding_service = EmbeddingService()
storage = VectorStorage(embedding_service, vector_dim=3072)

results = storage.find_similar_code(
    query="test",
    project_id=None,  # Try None first to test all chunks
    k=20
)

for i, result in enumerate(results):
    print(f"\nResult {i+1}:")
    print(f"  Score: {result['score']}")
    print(f"  File:  {result['file_path']}")
    print(f"  Name:  {result['name']}")
    print(f"  Project ID: {result.get('project_id', '???')}")
    print(f"  Chunk Type: {result.get('chunk_type')}")

