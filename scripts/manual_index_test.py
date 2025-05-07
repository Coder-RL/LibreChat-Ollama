import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.embedding_service import EmbeddingService
from app.services.vector_storage import VectorStorage

# Initialize services
embedding_service = EmbeddingService()
storage = VectorStorage(embedding_service=embedding_service)

# Known test content
code = '''
def hello_world():
    print("Hello, world!")
'''

# Generate and truncate embedding
embedding = embedding_service.generate_embedding(code)
embedding = embedding[:3072]  # Force 3072d for OpenSearch index compatibility

# Index the dummy code chunk
doc_id = storage.store_code_chunk(
    content=code,
    file_path="manual_test.py",
    chunk_type="function",
    name="hello_world",
    start_line=1,
    end_line=3,
    project_id="default",
    embedding_model="deepseek-coder:6.7b",  # model name traceability
    embedding=embedding
)

if doc_id:
    print(f"✅ Successfully stored test chunk with ID: {doc_id}")
else:
    print("❌ Failed to store test chunk")

