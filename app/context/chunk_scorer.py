"""
ChunkRelevanceScorer for scoring code chunks based on relevance to a query.
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from app.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChunkRelevanceScorer:
    """
    Service for scoring code chunks based on relevance to a query.
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize the chunk relevance scorer.
        
        Args:
            embedding_service: The embedding service to use
        """
        self.embedding_service = embedding_service or EmbeddingService()
        logger.info("Initialized ChunkRelevanceScorer")
        
        # Define AST type boost factors
        self.ast_boosts = {
            # High relevance
            "class": 0.15,
            "function": 0.15,
            "method": 0.15,
            
            # Medium relevance
            "variable": 0.05,
            "constant": 0.05,
            "property": 0.05,
            
            # Low relevance
            "import": -0.1,
            "comment": -0.1,
            "docstring": 0.0,
            
            # Default
            "default": 0.0
        }
        
        # Define file type boost factors
        self.file_type_boosts = {
            # Code files
            ".py": 0.1,
            ".js": 0.1,
            ".ts": 0.1,
            ".jsx": 0.1,
            ".tsx": 0.1,
            
            # Config files
            ".json": 0.05,
            ".yaml": 0.05,
            ".yml": 0.05,
            
            # Documentation
            ".md": -0.05,
            ".txt": -0.05,
            
            # Default
            "default": 0.0
        }
    
    def score_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score code chunks based on relevance to the query.
        
        Args:
            query: The query to score against
            chunks: The code chunks to score
            
        Returns:
            The scored code chunks, sorted by relevance
        """
        if not chunks:
            logger.warning("No chunks provided for scoring")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed(query)
            
            # Score each chunk
            for chunk in chunks:
                # Get or generate chunk embedding
                chunk_embedding = chunk.get("embedding")
                if chunk_embedding is None:
                    chunk_content = chunk.get("content", "")
                    chunk_embedding = self.embedding_service.embed(chunk_content)
                    chunk["embedding"] = chunk_embedding
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                
                # Apply AST type boost
                ast_type = chunk.get("ast_type", "default")
                ast_boost = self.ast_boosts.get(ast_type, self.ast_boosts["default"])
                
                # Apply file type boost
                file_path = chunk.get("file_path", "")
                file_ext = os.path.splitext(file_path)[1].lower()
                file_boost = self.file_type_boosts.get(file_ext, self.file_type_boosts["default"])
                
                # Calculate final score
                final_score = similarity + ast_boost + file_boost
                
                # Store the score components for debugging
                chunk["score"] = final_score
                chunk["similarity"] = similarity
                chunk["ast_boost"] = ast_boost
                chunk["file_boost"] = file_boost
            
            # Sort chunks by score (descending)
            scored_chunks = sorted(chunks, key=lambda c: c["score"], reverse=True)
            
            logger.info(f"Scored {len(chunks)} chunks, top score: {scored_chunks[0]['score'] if scored_chunks else 'N/A'}")
            return scored_chunks
        
        except Exception as e:
            logger.error(f"Error scoring chunks: {str(e)}")
            return chunks
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Cosine similarity (between -1 and 1)
        """
        if v1 is None or v2 is None:
            return 0.0
        
        try:
            # Convert to numpy arrays if needed
            if not isinstance(v1, np.ndarray):
                v1 = np.array(v1)
            if not isinstance(v2, np.ndarray):
                v2 = np.array(v2)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            return dot_product / (norm_v1 * norm_v2)
        
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
