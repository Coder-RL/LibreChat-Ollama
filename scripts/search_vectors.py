# /Users/robertlee/GitHubProjects/ollama-inference-app/scripts/search_vectors.py
#!/usr/bin/env python3
import os
import sys
import logging
import argparse

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
                return embedding[:self.target_dim]
        return embedding

def main():
    parser = argparse.ArgumentParser(description="Search vector embeddings")
    parser.add_argument("query", help="Query text to search for")
    parser.add_argument("--project-id", default="ollama-app", help="Project identifier")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()
    
    # Initialize services
    embedding_service = DimensionFixEmbeddingService(target_dim=3072)
    vector_storage = VectorStorage(
        embedding_service=embedding_service,
        index_name_prefix="code_vectors",
        vector_dim=3072
    )
    
    # Search for similar code
    results = vector_storage.find_similar_code(
        query=args.query,
        project_id=args.project_id,
        k=args.limit
    )
    
    logger.info(f"Found {len(results)} results for query: {args.query}")
    
    for i, result in enumerate(results):
        logger.info(f"\nResult {i+1}: {result.get('name')} (Score: {result.get('score', 0):.4f})")
        logger.info(f"File: {result.get('file_path')}")
        
        # Trim content if too long for display
        content = result.get('content', '')
        if len(content) > 200:
            content = content[:200] + "..."
        
        logger.info(f"Content Preview: {content}")
        logger.info("-" * 50)

if __name__ == "__main__":
    main()