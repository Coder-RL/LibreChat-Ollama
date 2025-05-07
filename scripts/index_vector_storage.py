#!/usr/bin/env python3
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.services.embedding_service import EmbeddingService
from app.services.vector_storage import VectorStorage

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DimensionFixEmbeddingService(EmbeddingService):
    """An embedding service that ensures dimension compatibility."""
    
    def __init__(self, target_dim=3072):
        super().__init__()
        self.target_dim = target_dim
    
    def generate_embedding(self, text):
        """Generate embedding and ensure it has the right dimension."""
        embedding = super().generate_embedding(text)
        if embedding is not None:
            # Truncate to target dimension if needed
            if len(embedding) > self.target_dim:
                logger.info(f"Truncating embedding from {len(embedding)} to {self.target_dim}")
                return embedding[:self.target_dim]
        return embedding

def main():
    # Read vector_storage.py
    vector_storage_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'app', 'services', 'vector_storage.py'
    )
    
    with open(vector_storage_path, 'r') as f:
        content = f.read()
    
    # Initialize services
    embedding_service = DimensionFixEmbeddingService(target_dim=3072)
    vector_storage = VectorStorage(
        embedding_service=embedding_service,
        index_name_prefix="code_vectors",
        vector_dim=3072
    )
    
    # Index the VectorStorage class
    doc_id = vector_storage.store_code_chunk(
        content=content,
        file_path="app/services/vector_storage.py",
        chunk_type="class",
        name="VectorStorage",
        project_id="ollama-app"
    )
    
    if doc_id:
        logger.info(f"Successfully indexed VectorStorage class with ID: {doc_id}")
    else:
        logger.error("Failed to index VectorStorage class")
    
    # Try searching for it
    results = vector_storage.find_similar_code(
        query="vector storage with flexible dimensions",
        project_id="ollama-app",
        k=5
    )
    
    logger.info(f"Found {len(results)} similar code chunks")
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}: {result.get('name')} (Score: {result.get('score', 0):.4f})")

if __name__ == "__main__":
    main()