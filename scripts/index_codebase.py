#!/usr/bin/env python3
import os
import sys
import argparse
import logging
import time
from typing import Dict, Any, List, Optional

# Make sure this path addition is at the very top
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Rest of imports
from app.services.embedding_service import EmbeddingService
from app.services.vector_storage import VectorStorage
from app.services.ast_rag import AstRagService

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



# Function definition starts at indent 0
def index_python_file(file_path: str, rel_path: str, project_id: str, 
                     ast_rag: AstRagService, vector_storage: VectorStorage) -> Dict[str, int]:
    """
    Index a single Python file.
    
    Args:
        file_path: Absolute path to the file
        rel_path: Relative path from project root
        project_id: Project identifier
        ast_rag: AST-based code analysis service
        vector_storage: Vector storage service
        
    Returns:
        Dict with counts of chunks and relationships indexed
    """
    logger.info(f"Indexing file: {rel_path}")
    
    # Define storable chunk types
    STORABLE_CHUNK_TYPES = {"function", "class", "method"}
    
    try:
        # Use AST to extract code chunks and relationships
        result = ast_rag._analyze_python_file(
            file_path=file_path,
            rel_path=rel_path,
            project_id=project_id
        )
        
        # Handle None result (for empty files)
        if result is None:
            logger.warning(f"No analysis results for {rel_path} (possibly empty file)")
            return {"chunks_found": 0, "chunks_stored": 0, "relationships": 0}
        
        # Unpack results safely
        chunks, relationships = result
        
        # Handle None chunks or relationships
        chunks = chunks or []
        relationships = relationships or {}
        
        # Store code chunks with vector embeddings
        chunks_stored = 0
        for chunk in chunks:
            # Check if we have all required fields
            if not chunk or 'chunk_type' not in chunk:
                continue
                
            chunk_type = chunk.get('chunk_type')
            # Skip non-storable chunk types
            if chunk_type not in STORABLE_CHUNK_TYPES:
                continue
                
            doc_id = vector_storage.store_code_chunk(
                content=chunk.get("content", ""),
                file_path=chunk.get("file_path", rel_path),
                chunk_type=chunk_type,
                name=chunk.get("name"),
                start_line=chunk.get("start_line"),
                end_line=chunk.get("end_line"),
                project_id=project_id,
                id=chunk.get("id")
            )
            
            if doc_id:
                chunks_stored += 1
        
        return {
            "chunks_found": len(chunks),
            "chunks_stored": chunks_stored,
            "relationships": len(relationships)
        }
    except Exception as e:
        logger.error(f"Error processing {rel_path}: {e}")
        return {"chunks_found": 0, "chunks_stored": 0, "relationships": 0}

def index_directory(directory: str, project_id: str, 
                    ast_rag: AstRagService, vector_storage: VectorStorage) -> Dict[str, Any]:
    """
    Recursively index Python files in a directory.
    
    Args:
        directory: Directory to scan for Python files
        project_id: Project identifier
        ast_rag: AST-based code analysis service
        vector_storage: Vector storage service
        
    Returns:
        Dict with summary statistics
    """
    total_stats = {
        "files_total": 0,
        "files_processed": 0,
        "chunks_found": 0,
        "chunks_stored": 0,
        "relationships": 0,
        "errors": []
    }
    
    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                total_stats["files_total"] += 1
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                
                try:
                    # Index the file
                    file_stats = index_python_file(
                        file_path=file_path,
                        rel_path=rel_path,
                        project_id=project_id,
                        ast_rag=ast_rag,
                        vector_storage=vector_storage
                    )
                    
                    # Update total stats
                    total_stats["files_processed"] += 1
                    total_stats["chunks_found"] += file_stats["chunks_found"]
                    total_stats["chunks_stored"] += file_stats["chunks_stored"]
                    total_stats["relationships"] += file_stats["relationships"]
                    
                except Exception as e:
                    logger.error(f"Error processing {rel_path}: {e}")
                    total_stats["errors"].append({
                        "file": rel_path,
                        "error": str(e)
                    })
    
    return total_stats

def main():
    parser = argparse.ArgumentParser(description="Index Python codebase for vector search")
    parser.add_argument("directory", help="Directory containing Python code to index")
    parser.add_argument("--project-id", default="default", help="Project identifier")
    parser.add_argument("--dimension", type=int, default=None, help="Vector dimension (auto-detected if not specified)")
    parser.add_argument("--clean", action="store_true", help="Clean existing project data before indexing")
    args = parser.parse_args()
    
    # Initialize services
    embedding_service = EmbeddingService()
    
    vector_storage = VectorStorage(
        embedding_service=embedding_service,
        index_name_prefix="code_vectors",
        vector_dim=args.dimension
    )
    
    ast_rag = AstRagService()
    
    logger.info(f"Initialized services. Vector dimension: {vector_storage.vector_dim}")
    
    # Clean existing data if requested
    if args.clean:
        logger.info(f"Cleaning existing data for project {args.project_id}")
        vector_storage.delete_by_project(args.project_id)
    
    # Start indexing
    start_time = time.time()
    logger.info(f"Starting indexing of {args.directory} for project {args.project_id}")
    
    stats = index_directory(
        directory=args.directory,
        project_id=args.project_id,
        ast_rag=ast_rag,
        vector_storage=vector_storage
    )
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    logger.info(f"Indexing completed in {elapsed_time:.2f} seconds")
    logger.info(f"Files processed: {stats['files_processed']}/{stats['files_total']}")
    logger.info(f"Code chunks found: {stats['chunks_found']}")
    logger.info(f"Code chunks stored: {stats['chunks_stored']}")
    logger.info(f"Relationships detected: {stats['relationships']}")
    
    if stats["errors"]:
        logger.warning(f"Errors encountered: {len(stats['errors'])}")
        for i, error in enumerate(stats["errors"][:5]):
            logger.warning(f"  {i+1}. {error['file']}: {error['error']}")
        
        if len(stats["errors"]) > 5:
            logger.warning(f"  ... and {len(stats['errors']) - 5} more errors")

if __name__ == "__main__":
    main()