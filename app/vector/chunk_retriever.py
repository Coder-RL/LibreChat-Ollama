"""
ChunkRetriever for retrieving code chunks from vector storage.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChunkRetriever:
    """
    Service for retrieving code chunks from vector storage.
    """
    
    def __init__(self, vector_storage=None):
        """
        Initialize the chunk retriever.
        
        Args:
            vector_storage: The vector storage service to use
        """
        self.vector_storage = vector_storage
        logger.info("Initialized ChunkRetriever")
    
    def get_chunks(self, query: str = None, project_id: str = None, k: int = 20) -> List[Dict[str, Any]]:
        """
        Get code chunks from vector storage.
        
        Args:
            query: The query to search for (if None, returns all chunks)
            project_id: The project identifier
            k: The number of results to return
            
        Returns:
            List of code chunks
        """
        try:
            if self.vector_storage is None:
                logger.warning("Vector storage not initialized")
                return []
            
            if query:
                # Search for similar code chunks
                chunks = self.vector_storage.find_similar_code(
                    query=query,
                    project_id=project_id,
                    k=k
                )
            else:
                # Get all chunks for the project
                chunks = self.vector_storage.get_all_chunks(project_id=project_id, limit=k)
            
            logger.info(f"Retrieved {len(chunks)} chunks for project {project_id}")
            return chunks
        
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            return []
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific code chunk by ID.
        
        Args:
            chunk_id: The ID of the chunk to retrieve
            
        Returns:
            The code chunk if found, None otherwise
        """
        try:
            if self.vector_storage is None:
                logger.warning("Vector storage not initialized")
                return None
            
            chunk = self.vector_storage.get_chunk_by_id(chunk_id)
            return chunk
        
        except Exception as e:
            logger.error(f"Error retrieving chunk {chunk_id}: {str(e)}")
            return None
