#!/usr/bin/env python3
# /Users/robertlee/GitHubProjects/ollama-inference-app/scripts/index_key_classes.py

import os
import sys
import logging
import argparse
import ast
from typing import Tuple, Optional

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
                logger.info(f"Truncating embedding from {len(embedding)} to {self.target_dim} dimensions")
                return embedding[:self.target_dim]
        return embedding

def extract_class_from_file(file_path: str, class_name: str) -> Tuple[Optional[str], int, int]:
    """
    Extract a specific class definition from a Python file.
    
    Args:
        file_path: Path to the Python file
        class_name: Name of the class to extract
        
    Returns:
        Tuple of (class_source, start_line, end_line)
    """
    try:
        with open(file_path, 'r') as f:
            source = f.read()
            
        # Parse the AST
        tree = ast.parse(source)
        
        # Find the class definition
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # Get line numbers
                start_line = node.lineno
                end_line = 0
                
                # Find the end line by traversing the AST
                for child in ast.walk(node):
                    if hasattr(child, 'lineno'):
                        end_line = max(end_line, child.lineno)
                
                # Get the source lines
                lines = source.splitlines()
                class_source = '\n'.join(lines[start_line-1:end_line])
                
                return class_source, start_line, end_line
                
        logger.warning(f"Class '{class_name}' not found in {file_path}")
        return None, 0, 0
        
    except Exception as e:
        logger.error(f"Error extracting class from {file_path}: {e}")
        return None, 0, 0

def index_class(file_path: str, class_name: str, project_id: str) -> Optional[str]:
    """
    Extract and index a specific class.
    
    Args:
        file_path: Path to the Python file
        class_name: Name of the class to extract
        project_id: Project identifier
        
    Returns:
        Document ID if successful, None otherwise
    """
    # Extract the class
    class_source, start_line, end_line = extract_class_from_file(file_path, class_name)
    
    if not class_source:
        return None
    
    # Initialize services
    embedding_service = DimensionFixEmbeddingService(target_dim=3072)
    vector_storage = VectorStorage(
        embedding_service=embedding_service,
        index_name_prefix="code_vectors",
        vector_dim=3072
    )
    
    # Store the class
    doc_id = vector_storage.store_code_chunk(
        content=class_source,
        file_path=file_path,
        chunk_type="class",
        name=class_name,
        start_line=start_line,
        end_line=end_line,
        project_id=project_id
    )
    
    return doc_id

def main():
    parser = argparse.ArgumentParser(description="Index key classes for vector search")
    parser.add_argument("--project-id", default="ollama-app", help="Project identifier")
    args = parser.parse_args()
    
    # Define key classes to index
    key_classes = [
        {
            "file_path": "app/services/vector_storage.py",
            "class_name": "VectorStorage"
        },
        {
            "file_path": "app/services/opensearch_client.py",
            "class_name": "OpenSearchClient"
        },
        {
            "file_path": "app/services/embedding_service.py",
            "class_name": "EmbeddingService"
        },
        {
            "file_path": "app/services/attention_manager.py",
            "class_name": "AttentionManager"
        }
    ]
    
    # Index each class
    for cls in key_classes:
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            cls["file_path"]
        )
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
            
        logger.info(f"Indexing {cls['class_name']} from {cls['file_path']}...")
        doc_id = index_class(file_path, cls["class_name"], args.project_id)
        
        if doc_id:
            logger.info(f"Successfully indexed {cls['class_name']} with ID: {doc_id}")
        else:
            logger.error(f"Failed to index {cls['class_name']}")

if __name__ == "__main__":
    main()