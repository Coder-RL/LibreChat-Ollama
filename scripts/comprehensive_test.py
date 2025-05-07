import os
import uuid
import logging
import sys
import time
from app.services.file_scanner import FileScanner
from app.services.gitignore_handler import GitignoreHandler
from app.services.vector_storage import VectorStorage
from app.services.database_storage import DatabaseStorage
from app.services.embedding_service import OllamaEmbeddingService
from app.services.ingestion_orchestrator import IngestionOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

logger = logging.getLogger(__name__)

# Base directory for tests
BASE_DIR = "/Users/robertlee/GitHubProjects/ollama-inference-app"
TEST_DIR = os.path.join(BASE_DIR, "test_dir")
MANY_FILES_DIR = os.path.join(BASE_DIR, "many_files")
NONEXISTENT_DIR = os.path.join(BASE_DIR, "nonexistent_directory")
TEST_GITIGNORE = os.path.join(BASE_DIR, "test_gitignore")
VALID_PROJECT_ID = "4dd62264-7005-4c78-983e-565c271eec2a"
INVALID_PROJECT_ID = "invalid-project-id"

def setup():
    """Set up test environment"""
    # Create test directory if it doesn't exist
    os.makedirs(TEST_DIR, exist_ok=True)
    
    # Create a large file (5MB)
    large_file_path = os.path.join(TEST_DIR, "large_test_file.txt")
    if not os.path.exists(large_file_path):
        with open(large_file_path, 'w') as f:
            f.write('This is a test line.\n' * 200000)
    
    # Create a small file
    small_file_path = os.path.join(TEST_DIR, "small_file.txt")
    with open(small_file_path, 'w') as f:
        f.write("This is a small test file.")
    
    # Create many files directory
    os.makedirs(MANY_FILES_DIR, exist_ok=True)
    for i in range(1, 51):
        with open(os.path.join(MANY_FILES_DIR, f"file_{i}.txt"), 'w') as f:
            f.write(f"This is file {i}")
    
    # Create a gitignore that excludes everything
    with open(TEST_GITIGNORE, 'w') as f:
        f.write("**/*")
    
    logger.info("Test environment set up successfully")

def test_large_file():
    """Test ingestion of a large file"""
    logger.info("=== Testing Large File Ingestion ===")
    
    embedding_service = OllamaEmbeddingService()
    vector_storage = VectorStorage(embedding_service=embedding_service)
    database_storage = DatabaseStorage()
    
    large_file_path = os.path.join(TEST_DIR, "large_test_file.txt")
    
    with open(large_file_path, 'r') as f:
        content = f.read()
    
    start_time = time.time()
    
    # Try to store the large file
    opensearch_id = vector_storage.store_code_chunk(
        content=content,
        file_path=large_file_path,
        chunk_type="file",
        name="large_test_file.txt",
        project_id=VALID_PROJECT_ID
    )
    
    db_id = database_storage.save_code_chunk(
        content=content,
        file_path=large_file_path,
        chunk_type="file",
        name="large_test_file.txt",
        project_id=VALID_PROJECT_ID
    )
    
    end_time = time.time()
    
    logger.info(f"Large file ingestion took {end_time - start_time:.2f} seconds")
    logger.info(f"OpenSearch ID: {opensearch_id}")
    logger.info(f"Database ID: {db_id}")
    
    return opensearch_id is not None and db_id is not None

def test_missing_directory():
    """Test ingestion with a missing directory"""
    logger.info("=== Testing Missing Directory ===")
    
    try:
        orchestrator = IngestionOrchestrator(
            base_directory=NONEXISTENT_DIR,
            project_id=VALID_PROJECT_ID
        )
        orchestrator.ingest_project()
        logger.error("Expected an error for missing directory, but none was raised")
        return False
    except Exception as e:
        logger.info(f"Expected error for missing directory: {e}")
        return True

def test_invalid_project_id():
    """Test ingestion with an invalid project ID"""
    logger.info("=== Testing Invalid Project ID ===")
    
    embedding_service = OllamaEmbeddingService()
    vector_storage = VectorStorage(embedding_service=embedding_service)
    database_storage = DatabaseStorage()
    
    small_file_path = os.path.join(TEST_DIR, "small_file.txt")
    
    with open(small_file_path, 'r') as f:
        content = f.read()
    
    # Try to store with invalid project ID
    try:
        opensearch_id = vector_storage.store_code_chunk(
            content=content,
            file_path=small_file_path,
            chunk_type="file",
            name="small_file.txt",
            project_id=INVALID_PROJECT_ID
        )
        
        logger.info(f"OpenSearch storage with invalid project ID: {opensearch_id}")
        
        db_id = database_storage.save_code_chunk(
            content=content,
            file_path=small_file_path,
            chunk_type="file",
            name="small_file.txt",
            project_id=INVALID_PROJECT_ID
        )
        
        logger.info(f"Database storage with invalid project ID: {db_id}")
        
        return opensearch_id is not None  # We expect OpenSearch to succeed even with invalid project ID
    except Exception as e:
        logger.error(f"Unexpected error with invalid project ID: {e}")
        return False

def test_gitignore_conflicts():
    """Test ingestion with a gitignore that excludes everything"""
    logger.info("=== Testing Gitignore Conflicts ===")
    
    gitignore_handler = GitignoreHandler(TEST_GITIGNORE)
    file_scanner = FileScanner(TEST_DIR)
    
    files = file_scanner.scan_files()
    logger.info(f"Found {len(files)} files before gitignore filtering")
    
    filtered_files = gitignore_handler.filter_ignored_files(files)
    logger.info(f"Found {len(filtered_files)} files after gitignore filtering")
    
    return len(filtered_files) == 0  # We expect all files to be filtered out

def test_many_files():
    """Test ingestion of many files"""
    logger.info("=== Testing Many Files Ingestion ===")
    
    orchestrator = IngestionOrchestrator(
        base_directory=MANY_FILES_DIR,
        project_id=VALID_PROJECT_ID
    )
    
    start_time = time.time()
    orchestrator.ingest_project()
    end_time = time.time()
    
    logger.info(f"Ingestion of {len(os.listdir(MANY_FILES_DIR))} files took {end_time - start_time:.2f} seconds")
    logger.info(f"OpenSearch success: {orchestrator.success_opensearch}")
    logger.info(f"PostgreSQL success: {orchestrator.success_postgresql}")
    logger.info(f"OpenSearch failures: {orchestrator.failed_opensearch}")
    logger.info(f"PostgreSQL failures: {orchestrator.failed_postgresql}")
    
    return orchestrator.success_opensearch > 0 and orchestrator.success_postgresql > 0

def test_db_failure():
    """Test database failure scenario"""
    logger.info("=== Testing Database Failure ===")
    
    embedding_service = OllamaEmbeddingService()
    vector_storage = VectorStorage(embedding_service=embedding_service)
    
    # Create a database storage with an invalid connection
    invalid_db_storage = DatabaseStorage()
    invalid_db_storage.db.engine = None  # Simulate a broken connection
    
    small_file_path = os.path.join(TEST_DIR, "small_file.txt")
    
    with open(small_file_path, 'r') as f:
        content = f.read()
    
    # First, store in OpenSearch only
    opensearch_id = vector_storage.store_code_chunk(
        content=content,
        file_path=small_file_path,
        chunk_type="file",
        name="small_file.txt",
        project_id=VALID_PROJECT_ID
    )
    
    logger.info(f"OpenSearch storage result: {opensearch_id}")
    
    # Now try with the invalid database
    try:
        db_id = invalid_db_storage.save_code_chunk(
            content=content,
            file_path=small_file_path,
            chunk_type="file",
            name="small_file.txt",
            project_id=VALID_PROJECT_ID
        )
        logger.info(f"Database storage result (should fail): {db_id}")
        return False  # We expect this to fail
    except Exception as e:
        logger.info(f"Expected database error: {e}")
        return True

def run_all_tests():
    """Run all tests and report results"""
    setup()
    
    results = {
        "Large File Test": test_large_file(),
        "Missing Directory Test": test_missing_directory(),
        "Invalid Project ID Test": test_invalid_project_id(),
        "Gitignore Conflicts Test": test_gitignore_conflicts(),
        "Many Files Test": test_many_files(),
        "Database Failure Test": test_db_failure()
    }
    
    logger.info("\n=== Test Results ===")
    for test_name, result in results.items():
        logger.info(f"{test_name}: {'PASS' if result else 'FAIL'}")
    
    return results

if __name__ == "__main__":
    run_all_tests()
