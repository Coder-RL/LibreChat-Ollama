"""
Embedding Service for generating vector embeddings from text.
"""

import os
import logging
import numpy as np
import requests
from typing import List, Optional, Union, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating embeddings from text using Ollama's embedding API.
    """
    
    def __init__(self, model: str = "nomic-embed-text", dimensions: int = 3072):
        """
        Initialize the embedding service.
        
        Args:
            model: The embedding model to use
            dimensions: The dimension of the embeddings to generate
        """
        self.model = model
        self.dimensions = dimensions
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.endpoint = f"{self.base_url}/api/embeddings"
        logger.info(f"Initialized EmbeddingService with model={model}, dimensions={dimensions}")
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            A numpy array containing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            # Return a zero vector of the correct dimension
            return np.zeros(self.dimensions)
        
        try:
            response = requests.post(
                self.endpoint,
                json={"model": self.model, "prompt": text}
            )
            
            if response.status_code != 200:
                logger.error(f"Error from embedding API: {response.status_code} - {response.text}")
                return np.zeros(self.dimensions)
            
            data = response.json()
            embedding = data.get("embedding", [])
            
            # Ensure the embedding has the correct dimension
            if len(embedding) > self.dimensions:
                logger.warning(f"Truncating embedding from {len(embedding)} to {self.dimensions}")
                embedding = embedding[:self.dimensions]
            elif len(embedding) < self.dimensions:
                logger.warning(f"Padding embedding from {len(embedding)} to {self.dimensions}")
                padding = [0.0] * (self.dimensions - len(embedding))
                embedding.extend(padding)
            
            return np.array(embedding)
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return np.zeros(self.dimensions)
    
    def batch_embed(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of numpy arrays containing the embedding vectors
        """
        return [self.embed(text) for text in texts]
