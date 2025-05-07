"""
RoleAwareContextInjector for injecting relevant code chunks into prompts based on agent role.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from app.vector.chunk_retriever import ChunkRetriever
from app.context.chunk_scorer import ChunkRelevanceScorer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RoleAwareContextInjector:
    """
    Service for injecting relevant code chunks into prompts based on agent role.
    """
    
    def __init__(self, role: str = "default", retriever: Optional[ChunkRetriever] = None, 
                 scorer: Optional[ChunkRelevanceScorer] = None):
        """
        Initialize the role-aware context injector.
        
        Args:
            role: The agent role (e.g., "frontend", "backend", "refactor")
            retriever: The chunk retriever to use
            scorer: The chunk scorer to use
        """
        self.role = role.lower()
        self.retriever = retriever or ChunkRetriever()
        self.scorer = scorer or ChunkRelevanceScorer()
        
        # Define role-specific keywords for filtering
        self.role_keywords = {
            # Frontend-related keywords
            "frontend": [
                "ui", "view", "component", "html", "css", "jsx", "tsx", "react", 
                "angular", "vue", "dom", "style", "client", "browser"
            ],
            
            # Backend-related keywords
            "backend": [
                "controller", "service", "model", "api", "db", "database", "server", 
                "route", "endpoint", "query", "repository", "dao"
            ],
            
            # DevOps-related keywords
            "devops": [
                "deploy", "ci", "cd", "pipeline", "docker", "kubernetes", "k8s", 
                "container", "config", "env", "environment"
            ],
            
            # Security-related keywords
            "security": [
                "auth", "authentication", "authorization", "permission", "role", 
                "encrypt", "decrypt", "hash", "token", "jwt", "oauth"
            ],
            
            # Refactor role (keep all)
            "refactor": ["any"],
            
            # Default role (keep all)
            "default": ["any"]
        }
        
        # Define role-specific file patterns
        self.role_file_patterns = {
            # Frontend-related file patterns
            "frontend": [
                ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss", ".vue", 
                "component", "view", "page", "client", "front", "ui"
            ],
            
            # Backend-related file patterns
            "backend": [
                ".py", ".java", ".rb", ".go", ".php", ".cs", 
                "controller", "service", "model", "repository", "dao", 
                "api", "server", "backend"
            ],
            
            # DevOps-related file patterns
            "devops": [
                "Dockerfile", "docker-compose", ".yml", ".yaml", ".tf", 
                "pipeline", "deploy", "config", ".env", "k8s"
            ],
            
            # Security-related file patterns
            "security": [
                "auth", "security", "permission", "role", "encrypt", "policy"
            ],
            
            # Refactor role (keep all)
            "refactor": [],
            
            # Default role (keep all)
            "default": []
        }
        
        logger.info(f"Initialized RoleAwareContextInjector with role={role}")
    
    def inject(self, query: str, session_id: str, project_id: str, max_chunks: int = 10) -> List[Dict[str, Any]]:
        """
        Inject relevant code chunks into the prompt based on the agent role.
        
        Args:
            query: The query to search for
            session_id: The session identifier
            project_id: The project identifier
            max_chunks: The maximum number of chunks to inject
            
        Returns:
            List of relevant code chunks
        """
        try:
            # Retrieve all chunks for the project
            all_chunks = self.retriever.get_chunks(query=query, project_id=project_id, k=50)
            
            if not all_chunks:
                logger.warning(f"No chunks found for project {project_id}")
                return []
            
            # Filter chunks by role
            filtered_chunks = self._filter_by_role(all_chunks)
            
            if not filtered_chunks:
                logger.warning(f"No chunks matched role {self.role}, using all chunks")
                filtered_chunks = all_chunks
            
            # Score chunks by relevance
            scored_chunks = self.scorer.score_chunks(query=query, chunks=filtered_chunks)
            
            # Take the top N chunks
            top_chunks = scored_chunks[:max_chunks]
            
            logger.info(f"Injected {len(top_chunks)} chunks for role {self.role}")
            return top_chunks
        
        except Exception as e:
            logger.error(f"Error injecting context: {str(e)}")
            return []
    
    def _filter_by_role(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter chunks by role.
        
        Args:
            chunks: The chunks to filter
            
        Returns:
            Filtered chunks
        """
        # Get keywords and file patterns for the current role
        keywords = self.role_keywords.get(self.role, self.role_keywords["default"])
        file_patterns = self.role_file_patterns.get(self.role, self.role_file_patterns["default"])
        
        # If role is "any" or no patterns defined, return all chunks
        if "any" in keywords or (not keywords and not file_patterns):
            return chunks
        
        filtered_chunks = []
        
        for chunk in chunks:
            file_path = chunk.get("file_path", "").lower()
            content = chunk.get("content", "").lower()
            
            # Check if file path matches any of the role's file patterns
            file_match = any(pattern.lower() in file_path for pattern in file_patterns)
            
            # Check if content contains any of the role's keywords
            keyword_match = any(keyword.lower() in content for keyword in keywords)
            
            # Include chunk if it matches either file pattern or keyword
            if file_match or keyword_match:
                filtered_chunks.append(chunk)
        
        return filtered_chunks
