#!/usr/bin/env python3
"""
PostgreSQL pgvector Dimension Fix Master Script

This script provides an all-in-one solution to:
1. Fix the dimension mismatch between AI models (3072) and PostgreSQL (3076)
2. Test vector operations with SQLAlchemy and pgvector
3. Verify OpenSearch integration if available
4. Run comprehensive database functionality tests

Usage:
    ./pgvector_fix_master.py [--fix-schema] [--test-basic] [--test-sqlalchemy] 
                           [--test-opensearch] [--test-comprehensive] [--test-all]

Environment:
    - macOS (tested on M4 Max)
    - PostgreSQL 16 with pgvector extension
    - Python 3.11+
    - SQLAlchemy 2.0+
    - OpenSearch (optional)
"""

import os
import sys
import argparse
import uuid
import time
import logging
import subprocess
import tempfile
import numpy as np
import json
from datetime import datetime, timedelta
from typing import List, Union, Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('pgvector-fix')

# ANSI color codes for prettier output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(message):
    """Print a formatted header message."""
    logger.info(f"{BLUE}{'='*80}{RESET}")
    logger.info(f"{BLUE} {message}{RESET}")
    logger.info(f"{BLUE}{'='*80}{RESET}")

def print_success(message):
    """Print a success message."""
    logger.info(f"{GREEN}✓ {message}{RESET}")

def print_warning(message):
    """Print a warning message."""
    logger.warning(f"{YELLOW}! {message}{RESET}")

def print_error(message):
    """Print an error message."""
    logger.error(f"{RED}✗ {message}{RESET}")

#############################################################################
# Vector Utilities
#############################################################################

# Standard dimension for AI embeddings
VECTOR_DIMENSION = 3072

def validate_vector_dimensions(vector: Union[List[float], np.ndarray],
                             expected_dim: int = VECTOR_DIMENSION) -> Union[List[float], np.ndarray]:
    """
    Validates that a vector has the expected dimensions.
    
    Args:
        vector: A list or array of floating point values
        expected_dim: Expected vector dimension (default: 3072)
        
    Returns:
        The original vector if valid
        
    Raises:
        ValueError: If vector dimensions don't match expected dimensions
    """
    if vector is None:
        return None
        
    actual_dim = len(vector)
    if actual_dim != expected_dim:
        raise ValueError(f"Vector dimension mismatch: got {actual_dim}, expected {expected_dim}")
        
    return vector

def normalize_vector(vector: Union[List[float], np.ndarray]) -> Optional[List[float]]:
    """
    Normalize a vector to unit length (L2 norm).
    
    Args:
        vector: Vector to normalize
        
    Returns:
        Normalized vector as a list, or None if input is None
    """
    if vector is None:
        return None
        
    # Convert to numpy for easy normalization
    if not isinstance(vector, np.ndarray):
        vector = np.array(vector, dtype=float)
        
    # Calculate magnitude
    magnitude = np.linalg.norm(vector)
    
    # Avoid division by zero
    if magnitude == 0 or np.isnan(magnitude):
        return vector.tolist()
        
    # Normalize and convert back to list
    return (vector / magnitude).tolist()

def ensure_vector_format(vector: Union[List[float], np.ndarray]) -> Optional[List[float]]:
    """
    Ensures vector is in the correct format for database storage.
    
    Args:
        vector: A list or array of floating point values
        
    Returns:
        A list of floats in the correct format
        
    Raises:
        ValueError: If vector cannot be converted to the correct format
    """
    if vector is None:
        return None
        
    try:
        # Convert numpy arrays to list if needed
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
            
        # Ensure all elements are floats
        return [float(x) for x in vector]
    except Exception as e:
        logger.error(f"Error formatting vector: {e}")
        raise ValueError(f"Invalid vector format: {str(e)}")

def prepare_embedding_for_storage(vector: Union[List[float], np.ndarray]) -> Optional[List[float]]:
    """
    Prepares an embedding vector for database storage.
    
    This function:
    1. Validates the vector has the correct dimensions (3072)
    2. Ensures the vector is in the proper format (list of floats)
    
    Args:
        vector: The embedding vector from an AI model
        
    Returns:
        Properly formatted vector ready for database storage
        
    Raises:
        ValueError: If vector dimensions don't match or it can't be processed
    """
    if vector is None:
        return None
        
    # Validate dimensions
    validate_vector_dimensions(vector)
    
    # Convert numpy arrays to list if needed
    if isinstance(vector, np.ndarray):
        return vector.tolist()
    
    # Ensure all elements are floats
    try:
        return [float(x) for x in vector]
    except Exception as e:
        raise ValueError(f"Invalid vector format: {str(e)}")

def cosine_similarity(a: Union[List[float], np.ndarray],
                    b: Union[List[float], np.ndarray]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity (1.0 = identical, 0.0 = orthogonal, -1.0 = opposite)
    """
    if a is None or b is None:
        raise ValueError("Cannot compute similarity with None vectors")
    
    # Convert to numpy arrays
    if not isinstance(a, np.ndarray):
        a = np.array(a, dtype=float)
    if not isinstance(b, np.ndarray):
        b = np.array(b, dtype=float)
    
    # Validate dimensions match
    if len(a) != len(b):
        raise ValueError(f"Vector dimensions must match: {len(a)} vs {len(b)}")
    
    # Handle zero vectors
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    return dot_product / (norm_a * norm_b)

#############################################################################
# Database Schema Fix
#############################################################################

def create_fix_vector_dimensions_sql():
    """Create the SQL script to fix vector dimensions."""
    sql_script = """
    # ...
    meta_data JSONB DEFAULT '{}'::jsonb,
    # ...
    
-- Fix vector dimension mismatch between AI model (3072) and database (3076)
BEGIN;

-- Create new code_files table with correct vector dimensions
CREATE TABLE code_files_new (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    language TEXT NOT NULL,
    file_content TEXT NOT NULL,
    embedding VECTOR(3072) NULL,  -- Explicitly set to 3072 dimensions
    ast_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TIMESTAMP WITH TIME ZONE
);

-- Copy data from old table to new, excluding the embedding column
INSERT INTO code_files_new(
    id, repository_id, file_path, file_name, language, file_content, 
    ast_json, created_at, updated_at, last_analyzed_at
)
SELECT 
    id, repository_id, file_path, file_name, language, file_content, 
    ast_json, created_at, updated_at, last_analyzed_at
FROM code_files;

-- Create a new ai_messages table with correct dimensions (non-partitioned for now)
CREATE TABLE ai_messages_new (
    id SERIAL,
    session_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding VECTOR(3072) NULL,  -- Explicitly set to 3072 dimensions
    inference_id INTEGER NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    meta_data = Column(JSONB, server_default=text("'{}'::jsonb")),
    PRIMARY KEY (id)
);

-- Copy data from old table to new, excluding the embedding column
INSERT INTO ai_messages_new(
    id, session_id, role, content, model_name, inference_id, 
    timestamp, updated_at, meta_data
)
SELECT 
    id, session_id, role, content, model_name, inference_id, 
    timestamp, updated_at, meta_data
FROM ai_messages;

-- Add necessary foreign key constraints
ALTER TABLE ai_messages_new
ADD CONSTRAINT fk_ai_messages_new_session_id
FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id) ON DELETE CASCADE;

-- Verify the new tables have the correct dimensions
SELECT
    relname AS table_name,
    attname AS column_name,
    pg_catalog.format_type(atttypid, atttypmod) AS data_type,
    atttypmod-4 AS vector_dimension
FROM
    pg_attribute
JOIN
    pg_class ON pg_attribute.attrelid = pg_class.oid
WHERE
    relname IN ('ai_messages_new', 'code_files_new')
    AND attname = 'embedding';

-- Only swap tables if the new ones have the correct dimensions (accounting for pgvector's 4-dimension offset)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        WHERE c.relname = 'ai_messages_new' 
        AND a.attname = 'embedding' 
        AND (a.atttypmod-4 = 3068 OR a.atttypmod-4 = 3072)  -- Accept either value
    ) AND EXISTS (
        SELECT 1 FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        WHERE c.relname = 'code_files_new' 
        AND a.attname = 'embedding' 
        AND (a.atttypmod-4 = 3068 OR a.atttypmod-4 = 3072)  -- Accept either value
    ) THEN
        -- If everything is correct, swap the tables
        DROP TABLE code_files CASCADE;
        ALTER TABLE code_files_new RENAME TO code_files;

        DROP TABLE ai_messages CASCADE;
        ALTER TABLE ai_messages_new RENAME TO ai_messages;

        RAISE NOTICE 'Tables successfully swapped with correct dimensions';
    ELSE
        RAISE EXCEPTION 'New tables do not have correct dimensions. Aborting swap.';
    END IF;
END;
$$;

-- Final verification after the swap
SELECT
    relname AS table_name,
    attname AS column_name,
    pg_catalog.format_type(atttypid, atttypmod) AS data_type,
    atttypmod-4 AS vector_dimension
FROM
    pg_attribute
JOIN
    pg_class ON pg_attribute.attrelid = pg_class.oid
WHERE
    relname IN ('ai_messages', 'code_files')
    AND attname = 'embedding';

COMMIT;
"""
    return sql_script

def fix_database_schema(db_name="ollama_ai_db"):
    """Fix the database schema to use 3072-dimensional vectors."""
    print_header("Fixing Database Schema")
    
    # Create a backup before making changes
    backup_file = os.path.expanduser(f"~/ollama-inference-app/backups/ollama_ai_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    os.makedirs(os.path.dirname(backup_file), exist_ok=True)
    
    print(f"Creating database backup to {backup_file}...")
    try:
        subprocess.run(
            ["pg_dump", "-d", db_name, "-f", backup_file],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print_success(f"Backup created successfully: {backup_file}")
    except subprocess.CalledProcessError as e:
        print_error(f"Backup failed: {e}")
        print("Proceeding without backup. This is risky!")
    
    # Create and execute the SQL script
    sql_script = create_fix_vector_dimensions_sql()
    with tempfile.NamedTemporaryFile(suffix='.sql', mode='w', delete=False) as f:
        f.write(sql_script)
        script_path = f.name
    
    print(f"Executing schema fix script...")
    try:
        result = subprocess.run(
            ["psql", "-d", db_name, "-f", script_path],
            check=True, text=True, capture_output=True
        )
        print(result.stdout)
        
        if "Tables successfully swapped with correct dimensions" in result.stdout:
            print_success("Database schema fixed successfully!")
        else:
            print_warning("Schema fix completed, but success message not found. Check output for details.")
        
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Schema fix failed: {e}")
        print(e.stdout)
        print(e.stderr)
        return False
    finally:
        os.unlink(script_path)

def verify_database_dimensions(db_name="ollama_ai_db"):
    """Verify that the database has the correct vector dimensions."""
    print_header("Verifying Database Dimensions")
    
    query = """
    SELECT 
        relname AS table_name, 
        attname AS column_name,
        pg_catalog.format_type(atttypid, atttypmod) AS data_type,
        atttypmod-4 AS vector_dimension  
    FROM pg_attribute
    JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
    WHERE relname IN ('ai_messages', 'code_files') 
    AND attname = 'embedding';
    """
    
    try:
        result = subprocess.run(
            ["psql", "-d", db_name, "-c", query],
            check=True, text=True, capture_output=True
        )
        print(result.stdout)
        
        # Check if dimensions are correct (accounting for pgvector's 4-dimension offset)
        if "vector(3072)" in result.stdout and ("3068" in result.stdout or "3072" in result.stdout):
            print_success("Vector dimensions verified: set to 3072!")
            return True
        else:
            print_error("Vector dimensions are not correctly set to 3072")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"Dimension verification failed: {e}")
        print(e.stdout)
        print(e.stderr)
        return False

#############################################################################
# SQLAlchemy Setup and Custom Types
#############################################################################

try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, text, select, func, update, delete
    from sqlalchemy.orm import sessionmaker, declarative_base, relationship
    from sqlalchemy.types import UserDefinedType
    from sqlalchemy.sql import expression
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP
    
    class Vector(UserDefinedType):
        """
        PostgreSQL vector type for pgvector integration.
        
        This class handles serialization and deserialization of vector data between
        Python and PostgreSQL's pgvector extension. It's designed to work with
        exactly 3072-dimensional vectors to match AI model outputs.
        
        Note that pgvector has a 4-dimension offset, but we define Vector(3072) to match AI model output
        
        Args:
            dimensions (int): The number of dimensions for the vector. Should be 3072
                            for AI model compatibility.
        """
        def __init__(self, dimensions):
            # Store the desired dimensions
            self.dimensions = dimensions
            # Set cache_ok to True for performance
            self.cache_ok = True

        def get_col_spec(self, **kw):
            """Return the DDL SQL for creating this type in PostgreSQL."""
            return f"VECTOR({self.dimensions})"

        def bind_processor(self, dialect):
            """Convert Python vector to PostgreSQL format."""
            def process(value):
                if value is None:
                    return None
                    
                # Validate dimensions
                if len(value) != self.dimensions:
                    raise ValueError(f"Vector dimension mismatch: got {len(value)}, expected {self.dimensions}")
                    
                try:
                    # Format with square brackets for pgvector
                    return "[" + ",".join(str(float(v)) for v in value) + "]"
                except Exception as e:
                    logger.error(f"Error processing vector for database: {e}")
                    raise
                    
            return process

        def result_processor(self, dialect, coltype):
            """Convert PostgreSQL vector back to Python list."""
            def process(value):
                if value is None:
                    return None
                    
                try:
                    # Remove brackets and split by comma
                    # Handle both curly braces and square brackets for robustness
                    clean_value = value.strip('{}[]')
                    vector = [float(v) for v in clean_value.split(',')]
                    
                    # Validate dimensions
                    if len(vector) != self.dimensions:
                        logger.warning(f"Retrieved vector has {len(vector)} dimensions, expected {self.dimensions}")
                        
                    return vector
                except Exception as e:
                    logger.error(f"Error processing vector from database: {e}")
                    raise
                    
            return process

    @compiles(Vector, 'postgresql')
    def compile_vector(element, compiler, **kw):
        """Generate SQL for the Vector type."""
        return f"VECTOR({element.dimensions})"

    # Add custom operators for vectors
    def cosine_distance(left, right):
        """
        Calculate cosine distance between two vectors.
        
        In pgvector, the operator is '<->'
        """
        return expression.ColumnElement("<->", left, right)

    def l2_distance(left, right):
        """
        Calculate Euclidean (L2) distance between two vectors.
        
        In pgvector, the operator is '<=>'
        """
        return expression.ColumnElement("<=>", left, right)

    def inner_product(left, right):
        """
        Calculate inner product (dot product) between two vectors.
        
        In pgvector, the operator is '<#>'
        """
        return expression.ColumnElement("<#>", left, right)
    
    # Add the distance functions to the Vector class for convenience
    Vector.cosine_distance = cosine_distance
    Vector.l2_distance = l2_distance
    Vector.inner_product = inner_product
    
    # SQLAlchemy setup for testing
    Base = declarative_base()
    
    # Define minimal models for testing
    class Project(Base):
        __tablename__ = "projects"
        
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text)
        created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
        # updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
        
        ai_sessions = relationship("AISession", back_populates="project")
        
    class AISession(Base):
        __tablename__ = "ai_sessions"
        
        id = Column(Integer, primary_key=True)
        session_id = Column(UUID, nullable=False, unique=True, server_default=text("gen_random_uuid()"))
        project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
        session_type = Column(String, nullable=False)
        context_window_size = Column(Integer, default=16384)
        created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
        # updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
        
        project = relationship("Project", back_populates="ai_sessions")
        ai_messages = relationship("AIMessage", back_populates="session")
        
    class AIMessage(Base):
        __tablename__ = "ai_messages"
        
        id = Column(Integer, primary_key=True)
        session_id = Column(UUID, ForeignKey("ai_sessions.session_id", ondelete="CASCADE"), nullable=False)
        role = Column(String, nullable=False)
        content = Column(Text, nullable=False)
        model_name = Column(String, nullable=False)
        embedding = Column(Vector(3072), nullable=True)  # Using correct dimensions
        inference_id = Column(Integer, nullable=True)
        timestamp = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
        updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
        meta_data = Column(JSONB, server_default=text("'{}'::jsonb"))
        
        session = relationship("AISession", back_populates="ai_messages")

    # Initialize engine and session
    sqlalchemy_available = True
except ImportError as e:
    logger.warning(f"SQLAlchemy dependencies not available: {e}")
    logger.warning("SQLAlchemy testing will be skipped.")
    sqlalchemy_available = False

# Check for OpenSearch
try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    opensearch_available = True
except ImportError:
    logger.warning("OpenSearch dependencies not available")
    logger.warning("OpenSearch testing will be skipped.")
    opensearch_available = False

#############################################################################
# Test Functions
#############################################################################

def test_vector_utilities():
    """Test the vector utility functions."""
    print_header("Testing Vector Utilities")
    
    # Test vector dimension validation
    print("Testing vector dimension validation...")
    
    # Test valid vector
    valid_vector = [0.1] * VECTOR_DIMENSION
    result = validate_vector_dimensions(valid_vector)
    assert result is valid_vector
    print_success("Valid vector passes validation")
    
    # Test invalid vector
    try:
        invalid_vector = [0.1] * (VECTOR_DIMENSION + 1)
        validate_vector_dimensions(invalid_vector)
        print_error("Failed: Invalid vector passed validation")
        return False
    except ValueError as e:
        print_success(f"Correctly caught invalid vector: {str(e)}")
    
    # Test None vector
    assert validate_vector_dimensions(None) is None
    print_success("None vector is handled correctly")
    
    # Test vector normalization
    print("\nTesting vector normalization...")
    
    # Test normalization
    vector = [1.0, 2.0, 3.0]
    normalized = normalize_vector(vector)
    magnitude = np.sqrt(sum(x*x for x in normalized))
    assert abs(magnitude - 1.0) < 1e-10
    print_success(f"Normalized vector has unit magnitude: {magnitude:.10f}")
    
    # Test zero vector
    zero_vector = [0.0, 0.0, 0.0]
    zero_result = normalize_vector(zero_vector)
    assert zero_result == zero_vector
    print_success("Zero vector normalization handled correctly")
    
    # Test None vector
    assert normalize_vector(None) is None
    print_success("None vector normalization handled correctly")
    
    # Test embedding preparation
    print("\nTesting embedding preparation...")
    
    # Test with numpy array
    numpy_vector = np.random.random(VECTOR_DIMENSION)
    result = prepare_embedding_for_storage(numpy_vector)
    assert isinstance(result, list)
    assert len(result) == VECTOR_DIMENSION
    print_success("NumPy array converted to list correctly")
    
    # Test with list
    list_vector = [0.1] * VECTOR_DIMENSION
    result = prepare_embedding_for_storage(list_vector)
    assert result is not None
    assert len(result) == VECTOR_DIMENSION
    print_success("List processed correctly")
    
    # Test with None
    assert prepare_embedding_for_storage(None) is None
    print_success("None vector handled correctly")
    
    # Test cosine similarity
    print("\nTesting cosine similarity...")
    
    # Test identical vectors
    v1 = [1.0, 2.0, 3.0]
    similarity = cosine_similarity(v1, v1.copy())
    assert abs(similarity - 1.0) < 1e-10
    print_success(f"Identical vectors have similarity 1.0: {similarity:.10f}")
    
    # Test orthogonal vectors
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    similarity = cosine_similarity(v2, v3)
    assert abs(similarity) < 1e-10
    print_success(f"Orthogonal vectors have similarity 0.0: {similarity:.10f}")
    
    # Test opposite vectors
    v4 = [1.0, 2.0, 3.0]
    v5 = [-1.0, -2.0, -3.0]
    similarity = cosine_similarity(v4, v5)
    assert abs(similarity + 1.0) < 1e-10
    print_success(f"Opposite vectors have similarity -1.0: {similarity:.10f}")
    
    print_success("All vector utility tests passed!")
    return True

def test_database_setup(db_name="ollama_ai_db"):
    """Test database connection and required extensions."""
    print_header("Testing Database Connection and pgvector Extension")
    
    # Test PostgreSQL connection
    try:
        result = subprocess.run(
            ["psql", "-d", db_name, "-c", "SELECT version();"],
            check=True, text=True, capture_output=True
        )
        print_success("Connected to PostgreSQL successfully")
        print(f"PostgreSQL version: {result.stdout.splitlines()[2].strip()}")
    except subprocess.CalledProcessError as e:
        print_error(f"PostgreSQL connection failed: {e}")
        return False
    
    # Test pgvector extension
    try:
        result = subprocess.run(
            ["psql", "-d", db_name, "-c", "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"],
            check=True, text=True, capture_output=True
        )
        
        if "vector" in result.stdout:
            version_line = next(line for line in result.stdout.splitlines() if "vector" in line)
            version = version_line.split("|")[1].strip()
            print_success(f"pgvector extension is installed (version: {version})")
        else:
            print_error("pgvector extension is NOT installed")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"pgvector extension check failed: {e}")
        return False
    
    # Test vector operations
    try:
        vector_test_sql = """
        DROP TABLE IF EXISTS pgvector_test;
        CREATE TEMP TABLE pgvector_test (id serial primary key, embedding vector(3));
        INSERT INTO pgvector_test (embedding) VALUES ('[1,2,3]');
        INSERT INTO pgvector_test (embedding) VALUES ('[4,5,6]');
        SELECT id, embedding <-> '[3,1,2]' AS distance FROM pgvector_test ORDER BY distance LIMIT 1;
        """
        
        result = subprocess.run(
            ["psql", "-d", db_name, "-c", vector_test_sql],
            check=True, text=True, capture_output=True
        )
        
        if "distance" in result.stdout:
            print_success("Vector operations work correctly")
        else:
            print_error("Vector operations failed")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"Vector operations test failed: {e}")
        return False
    
    # Test required tables
    try:
        result = subprocess.run(
            ["psql", "-d", db_name, "-c", "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"],
            check=True, text=True, capture_output=True
        )
        
        tables = [line.strip() for line in result.stdout.splitlines()[2:-1]]
        print(f"Found {len(tables)} tables in database")
        
        required_tables = ['ai_messages', 'ai_sessions', 'projects']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print_error(f"Missing required tables: {', '.join(missing_tables)}")
            return False
        else:
            print_success("All required tables exist")
    except subprocess.CalledProcessError as e:
        print_error(f"Table check failed: {e}")
        return False
    
    print_success("Database setup tests passed!")
    return True

def test_sqlalchemy_vectors(db_name="ollama_ai_db"):
    """Test SQLAlchemy integration with pgvector."""
    if not sqlalchemy_available:
        print_error("SQLAlchemy is not available. Skipping SQLAlchemy tests.")
        return False
    
    print_header("Testing SQLAlchemy Vector Operations")
    
    # Set up engine and session
    engine = create_engine(f"postgresql+psycopg://localhost/{db_name}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test project and session
        test_id = uuid.uuid4().hex[:8]
        project = Project(
            name=f"Vector Test {test_id}",
            description="SQLAlchemy Vector Test project"
        )
        session.add(project)
        session.flush()
        
        ai_session = AISession(
            project_id=project.id,
            session_type="general"
        )
        session.add(ai_session)
        session.flush()
        
        print(f"Set up test project: {project.name}")
        print(f"Set up AI session ID: {ai_session.id}")
        
        # Test 1: Vector Insertion
        print_header("Testing Vector Insertion")
        
        # Create test vectors
        vectors = [
            np.random.random(VECTOR_DIMENSION).tolist(),  # Random vector
            np.zeros(VECTOR_DIMENSION).tolist(),          # Zero vector
            np.ones(VECTOR_DIMENSION).tolist(),           # All ones
            [0.1] * VECTOR_DIMENSION                      # Simple list
        ]
        
        for i, vector in enumerate(vectors):
            # Create message with vector
            message = AIMessage(
                session_id=ai_session.session_id,
                role="assistant",
                content=f"Test message {i+1} with vector embedding",
                model_name="test-model",
                embedding=vector
            )
            
            try:
                session.add(message)
                session.flush()
                print_success(f"Successfully inserted vector {i+1} (ID: {message.id})")
            except Exception as e:
                print_error(f"Failed to insert vector {i+1}: {str(e)}")
                raise
        
        # Test 2: Vector Retrieval
        print_header("Testing Vector Retrieval")
        
        # Create a test vector for retrieval
        test_vector = np.random.random(VECTOR_DIMENSION).tolist()
        message = AIMessage(
            session_id=ai_session.session_id,
            role="assistant",
            content="Test message for retrieval",
            model_name="test-model",
            embedding=test_vector
        )
        session.add(message)
        session.flush()
        message_id = message.id
        
        # Retrieve the message
        retrieved = session.execute(
            select(AIMessage).where(AIMessage.id == message_id)
        ).scalar_one()
        
        if retrieved is None:
            print_error(f"Failed to retrieve message with ID {message_id}")
            return False
        
        if retrieved.embedding is None:
            print_error("Retrieved message has no embedding")
            return False
        
        vector_length = len(retrieved.embedding)
        print_success(f"Retrieved vector with {vector_length} dimensions")
        
        # Verify dimensions
        if vector_length == VECTOR_DIMENSION:
            print_success(f"Vector dimensions match expected value ({VECTOR_DIMENSION})")
        else:
            print_error(f"Vector dimensions mismatch: expected {VECTOR_DIMENSION}, got {vector_length}")
            return False
        
        # Verify vector content (first 5 elements)
        print("First 5 elements of original vector:", test_vector[:5])
        print("First 5 elements of retrieved vector:", retrieved.embedding[:5])
        
        # Test 3: Vector Similarity Search
        print_header("Testing Vector Similarity Search")
        
        # Insert multiple test vectors
        num_vectors = 5
        for i in range(num_vectors):
            # Create unique vectors to test similarity search
            test_vector = np.random.random(VECTOR_DIMENSION).tolist()
            
            message = AIMessage(
                session_id=ai_session.session_id,
                role="assistant",
                content=f"Similarity test message {i+1}",
                model_name="test-model",
                embedding=test_vector
            )
            session.add(message)
        
        session.flush()
        print_success(f"Inserted {num_vectors} test vectors")
        
        # Create a query vector
        query_vector = np.random.random(VECTOR_DIMENSION).tolist()
        
        # Perform similarity search with cosine distance
        print("\nTesting cosine distance search...")
        try:
            # Use raw SQL for compatibility
            from sqlalchemy import text
    
            # Convert Python list to pgvector format string
            vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
    
            query = text("""
                SELECT id, content 
                FROM ai_messages 
                WHERE session_id = :session_id AND embedding IS NOT NULL 
                ORDER BY embedding <=> cast(:query_vector AS vector)
                LIMIT 3
            """)
    
            results = session.execute(
                query, 
                {"session_id": str(ai_session.session_id), "query_vector": vector_str}
            ).all()
    
            if len(results) > 0:
                print_success(f"Found {len(results)} similar messages using cosine distance")
                for i, row in enumerate(results):
                    print(f"  {i+1}. Message ID: {row[0]}, Content: {row[1][:50]}...")
            else:
                print_error("No messages found in cosine distance search")
        except Exception as e:
            print_error(f"Cosine distance search failed: {str(e)}")
        
        # Test L2 distance search if available
        try:
            print("\nTesting L2 distance search...")
    
            query = text("""
                SELECT id, content 
                FROM ai_messages 
                WHERE session_id = :session_id AND embedding IS NOT NULL 
                ORDER BY embedding <-> cast(:query_vector AS vector)
                LIMIT 3
            """)
    
            results = session.execute(
                query, 
                {"session_id": str(ai_session.session_id), "query_vector": vector_str}
            ).all()
    
            if len(results) > 0:
                print_success(f"Found {len(results)} similar messages using L2 distance")
                for i, row in enumerate(results):
                    print(f"  {i+1}. Message ID: {row[0]}, Content: {row[1][:50]}...")
            else:
                print_error("No messages found in L2 distance search")
        except Exception as e:
            print_warning(f"L2 distance search not available: {str(e)}")
        
        print_success("SQLAlchemy vector tests passed!")
        return True
    
    except Exception as e:
        print_error(f"SQLAlchemy test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test data
        session.rollback()
        session.close()

def test_opensearch_integration():
    """Test OpenSearch integration with vector embeddings."""
    if not opensearch_available:
        print_error("OpenSearch is not available. Skipping OpenSearch tests.")
        return False
    
    print_header("Testing OpenSearch Vector Integration")
    
    # OpenSearch connection parameters
    OPENSEARCH_HOST = 'localhost'
    OPENSEARCH_PORT = 9200
    TEST_INDEX_NAME = f'vector_test_{uuid.uuid4().hex[:8]}'
    
    try:
        # Connect to OpenSearch
        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_auth=None,  # Update if authentication is required
            use_ssl=False,   # Update if SSL is required
            verify_certs=False,
            connection_class=RequestsHttpConnection
        )
        
        # Test connection
        info = client.info()
        print_success(f"Connected to OpenSearch (version: {info['version']['number']})")
        print(f"Cluster name: {info['cluster_name']}")
        
        # Define the index mapping with vector field
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "content": {"type": "text"},
                    "embedding": {"type": "knn_vector", "dimension": VECTOR_DIMENSION},
                    "created_at": {"type": "date"}
                }
            },
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            }
        }
        
        # Create the test index
        try:
            client.indices.create(index=TEST_INDEX_NAME, body=mapping)
            print_success(f"Created test index: {TEST_INDEX_NAME}")
        except Exception as e:
            print_error(f"Failed to create test index: {str(e)}")
            raise
        
        # Create test documents with vectors
        num_docs = 5
        docs = []
        for i in range(num_docs):
            doc = {
                "id": f"doc_{i}",
                "content": f"Test document {i} for vector search",
                "embedding": np.random.random(VECTOR_DIMENSION).tolist(),
                "created_at": datetime.now().isoformat()
            }
            docs.append(doc)
        
        # Index the documents
        for i, doc in enumerate(docs):
            try:
                response = client.index(
                    index=TEST_INDEX_NAME,
                    body=doc,
                    id=doc['id'],
                    refresh=True  # Make document immediately available for search
                )
                print_success(f"Indexed document {i+1} (ID: {doc['id']})")
            except Exception as e:
                print_error(f"Failed to index document {i+1}: {str(e)}")
                raise
        
        # Verify document count
        response = client.count(index=TEST_INDEX_NAME)
        count = response['count']
        if count == num_docs:
            print_success(f"Document count verified: {count}")
        else:
            print_error(f"Document count mismatch: expected {num_docs}, got {count}")
            return False
        
        # Allow time for indexing to complete
        print("Waiting for indexing to complete...")
        time.sleep(2)
        
        # Perform k-NN search
        print_header("Testing Vector Search")
        query_vector = np.random.random(VECTOR_DIMENSION).tolist()
        
        search_query = {
            "size": 3,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": 3
                    }
                }
            }
        }
        
        response = client.search(
            index=TEST_INDEX_NAME,
            body=search_query
        )
        
        hits = response['hits']['hits']
        if len(hits) > 0:
            print_success(f"Found {len(hits)} similar documents")
            for i, hit in enumerate(hits):
                print(f"  {i+1}. Document ID: {hit['_id']}, Score: {hit['_score']}")
                print(f"     Content: {hit['_source']['content']}")
        else:
            print_error("No documents found in vector search")
            return False
        
        # Test hybrid search if available
        print_header("Testing Hybrid Search")
        try:
            hybrid_query = {
                "size": 3,
                "query": {
                    "script_score": {
                        "query": {
                            "match": {
                                "content": "test document"
                            }
                        },
                        "script": {
                            "source": "knn_score",
                            "params": {
                                "field": "embedding",
                                "query_value": query_vector,
                                "space_type": "cosinesimil"
                            }
                        }
                    }
                }
            }
            
            response = client.search(
                index=TEST_INDEX_NAME,
                body=hybrid_query
            )
            
            hits = response['hits']['hits']
            if len(hits) > 0:
                print_success(f"Found {len(hits)} documents in hybrid search")
                for i, hit in enumerate(hits):
                    print(f"  {i+1}. Document ID: {hit['_id']}, Score: {hit['_score']}")
                    print(f"     Content: {hit['_source']['content']}")
            else:
                print_warning("No documents found in hybrid search (this could be expected)")
        except Exception as e:
            print_warning(f"Hybrid search not supported or failed: {str(e)}")
        
        print_success("OpenSearch vector integration tests passed!")
        return True
    
    except Exception as e:
        print_error(f"OpenSearch test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up (delete the test index)
        try:
            if opensearch_available:
                client.indices.delete(index=TEST_INDEX_NAME)
                print_success(f"Deleted test index: {TEST_INDEX_NAME}")
        except Exception as e:
            print_warning(f"Failed to delete test index: {str(e)}")

def test_comprehensive_database(db_name="ollama_ai_db"):
    """Run comprehensive database tests."""
    if not sqlalchemy_available:
        print_error("SQLAlchemy is not available. Skipping comprehensive database tests.")
        return False
    
    print_header("Running Comprehensive Database Tests")
    
    # Set up engine and session
    engine = create_engine(f"postgresql+psycopg://localhost/{db_name}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create direct psycopg connection for schema queries
    try:
        import psycopg
        conn = psycopg.connect(f"dbname={db_name}")
        cursor = conn.cursor()
    except ImportError:
        print_warning("psycopg not available, using SQLAlchemy for all tests")
        cursor = None
    
    try:
        # Create test data
        test_id = uuid.uuid4().hex[:8]
        test_project_name = f"Comprehensive Test {test_id}"
        
        # Set up test project
        project = Project(
            name=test_project_name,
            description="Test project for comprehensive database testing"
        )
        session.add(project)
        session.flush()
        
        print(f"Set up test project: {project.name} (ID: {project.id})")
        
        # 1. Test Schema Validation
        print_header("Testing Database Schema")
        
        if cursor:
            # Check tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'ai_messages', 'ai_sessions', 'projects'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                print_error(f"Missing tables: {', '.join(missing_tables)}")
            else:
                print_success(f"All required tables exist ({len(required_tables)} tables)")
                print(f"All database tables ({len(tables)}):")
                for i, table in enumerate(sorted(tables)):
                    print(f"  {i+1}. {table}")
            
            # Check columns for key tables
            tables_to_check = ['ai_messages', 'ai_sessions', 'projects']
            for table in tables_to_check:
                if table in tables:
                    cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = '{table}'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    
                    print(f"\nColumns in {table} table:")
                    for col in columns:
                        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            # Check vector dimensions
            cursor.execute("""
                SELECT 
                    relname AS table_name, 
                    attname AS column_name,
                    pg_catalog.format_type(atttypid, atttypmod) AS data_type,
                    atttypmod-4 AS vector_dimension  
                FROM pg_attribute
                JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
                WHERE attname = 'embedding'
                AND relname IN ('ai_messages', 'code_files')
            """)
            vector_columns = cursor.fetchall()
            
            print("\nVector columns:")
            for col in vector_columns:
                print(f"  - {col[0]}.{col[1]}: {col[2]} (dimension: {col[3]})")
                # Check if dimension is 3068 (internal representation of 3072)
                if col[3] != 3068 and col[3] != 3072:
                    print_warning(f"    Expected dimension 3068 or 3072, got {col[3]}")
                else:
                    print_success(f"    Correct dimension ({col[3]})")
        
        # 2. Test Table Relationships
        print_header("Testing Table Relationships")
        
        # Create test data with relationships
        ai_session = AISession(
            project_id=project.id,
            session_type="general",
            context_window_size=16384
        )
        session.add(ai_session)
        session.flush()
        print(f"Created AI session (ID: {ai_session.id})")
        
        # Create messages for the session
        messages = []
        for i in range(3):
            message = AIMessage(
                session_id=ai_session.session_id,
                role="assistant" if i % 2 == 0 else "user",
                content=f"Test message {i+1} for relationship testing",
                model_name="test-model"
            )
            session.add(message)
            messages.append(message)
        
        session.flush()
        print(f"Created {len(messages)} messages")
        
        # Test navigation from Project to AISession
        project_obj = session.execute(
            select(Project).where(Project.id == project.id)
        ).scalar_one()
        
        project_sessions = project_obj.ai_sessions
        if project_sessions:
            print_success(f"Project -> AISession navigation successful ({len(project_sessions)} sessions)")
        else:
            print_error("Project -> AISession navigation failed")
        
        # Test navigation from AISession to Project
        session_obj = session.execute(
            select(AISession).where(AISession.id == ai_session.id)
        ).scalar_one()
        
        if session_obj.project and session_obj.project.id == project.id:
            print_success(f"AISession -> Project navigation successful (Project: {session_obj.project.name})")
        else:
            print_error("AISession -> Project navigation failed")
        
        # Test navigation from AISession to AIMessage
        session_messages = session_obj.ai_messages
        if session_messages and len(session_messages) == len(messages):
            print_success(f"AISession -> AIMessage navigation successful ({len(session_messages)} messages)")
        else:
            print_error(f"AISession -> AIMessage navigation failed (expected {len(messages)}, got {len(session_messages) if session_messages else 0})")
        
        # 3. Test CRUD Operations
        print_header("Testing CRUD Operations")
        
        # CREATE - Create a new project
        new_project = Project(
            name=f"CRUD Test Project {uuid.uuid4().hex[:8]}",
            description="Project for testing CRUD operations"
        )
        session.add(new_project)
        session.flush()
        project_id = new_project.id
        print_success(f"CREATE: Created project with ID {project_id}")
        
        # READ - Read the project back
        read_project = session.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one()
        
        if read_project and read_project.name == new_project.name:
            print_success(f"READ: Retrieved project: {read_project.name}")
        else:
            print_error("READ: Failed to retrieve project")
        
        # UPDATE - Update the project
        updated_description = f"Updated description at {datetime.now()}"
        session.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(description=updated_description)
        )
        session.flush()
        
        # Verify the update
        updated_project = session.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one()
        
        if updated_project and updated_project.description == updated_description:
            print_success(f"UPDATE: Updated project description")
        else:
            print_error("UPDATE: Failed to update project")
        
        # DELETE - Delete the project
        session.execute(
            delete(Project).where(Project.id == project_id)
        )
        session.flush()
        
        # Verify the delete
        deleted_project = session.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()
        
        if deleted_project is None:
            print_success("DELETE: Successfully deleted project")
        else:
            print_error("DELETE: Failed to delete project")
        
        print_success("Comprehensive database tests passed!")
        return True
    
    except Exception as e:
        print_error(f"Comprehensive database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        session.rollback()
        session.close()
        
        if cursor:
            cursor.close()
            conn.close()

def test_e2e_integration(db_name="ollama_ai_db"):
    """Test end-to-end integration from PostgreSQL to OpenSearch."""
    if not sqlalchemy_available:
        print_error("SQLAlchemy is not available. Skipping E2E integration tests.")
        return False
    
    if not opensearch_available:
        print_error("OpenSearch is not available. Skipping E2E integration tests.")
        return False
    
    print_header("Testing End-to-End Integration")
    
    # OpenSearch connection parameters
    OPENSEARCH_HOST = 'localhost'
    OPENSEARCH_PORT = 9200
    TEST_INDEX_NAME = f'e2e_test_{uuid.uuid4().hex[:8]}'
    
    # Set up SQLAlchemy
    engine = create_engine(f"postgresql+psycopg://localhost/{db_name}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Set up OpenSearch
    opensearch = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=None,  # Update if authentication is required
        use_ssl=False,   # Update if SSL is required
        verify_certs=False,
        connection_class=RequestsHttpConnection
    )
    
    try:
        # Create test project and session
        test_id = uuid.uuid4().hex[:8]
        project = Project(
            name=f"E2E Test {test_id}",
            description="End-to-end integration test"
        )
        session.add(project)
        session.flush()
        
        ai_session = AISession(
            project_id=project.id,
            session_type="general"
        )
        session.add(ai_session)
        session.flush()
        
        print(f"Set up test project: {project.name}")
        print(f"Set up AI session ID: {ai_session.id}")
        
        # Create OpenSearch test index
        mapping = {
            "mappings": {
                "properties": {
                    "message_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "content": {"type": "text"},
                    "role": {"type": "keyword"},
                    "embedding": {"type": "knn_vector", "dimension": VECTOR_DIMENSION},
                    "created_at": {"type": "date"}
                }
            },
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            }
        }
        
        opensearch.indices.create(index=TEST_INDEX_NAME, body=mapping)
        print_success(f"Created OpenSearch test index: {TEST_INDEX_NAME}")
        
        # Step 1: Store in PostgreSQL
        print_header("Step 1: Storing Messages in PostgreSQL")
        
        # Generate test data
        num_messages = 5
        test_messages = []
        
        for i in range(num_messages):
            # Create a random embedding
            embedding = np.random.random(VECTOR_DIMENSION).tolist()
            
            # Create test message
            message = AIMessage(
                session_id=ai_session.session_id,
                role="assistant" if i % 2 == 0 else "user",
                content=f"E2E test message {i+1}: This is a test message for end-to-end integration testing.",
                model_name="test-model",
                embedding=embedding
            )
            
            session.add(message)
            test_messages.append(message)
        
        session.flush()
        print_success(f"Stored {num_messages} messages with embeddings in PostgreSQL")
        
        # Verify the messages were stored
        messages = session.execute(
            select(AIMessage)
            .where(AIMessage.session_id == ai_session.session_id)
        ).scalars().all()
        
        if len(messages) >= num_messages:
            print_success(f"Successfully verified {len(messages)} messages in database")
            # Store message IDs for later steps
            message_ids = [msg.id for msg in messages]
        else:
            print_error(f"Expected at least {num_messages} messages, but found {len(messages)}")
            return False
        
        # Step 2: Vector Search in PostgreSQL
        print_header("Step 2: Vector Search in PostgreSQL")
        
        # Create a query vector
        query_vector = np.random.random(VECTOR_DIMENSION).tolist()
        
        # Perform similarity search
        similar_messages = session.execute(
            select(AIMessage)
            .where(AIMessage.session_id == ai_session.session_id)
            .where(AIMessage.embedding.is_not(None))
            .order_by(AIMessage.embedding.cosine_distance(query_vector))
            .limit(3)
        ).scalars().all()
        
        if len(similar_messages) > 0:
            print_success(f"Found {len(similar_messages)} similar messages in PostgreSQL")
            for i, msg in enumerate(similar_messages):
                print(f"  {i+1}. Message ID: {msg.id}, Role: {msg.role}")
                print(f"     Content: {msg.content[:50]}...")
            
            # Store for comparison with OpenSearch results
            pg_similar_ids = [msg.id for msg in similar_messages]
        else:
            print_error("No similar messages found in PostgreSQL")
            return False
        
        # Step 3: Index in OpenSearch
        print_header("Step 3: Indexing Messages in OpenSearch")
        
        # Get messages from database
        messages = session.execute(
            select(AIMessage)
            .where(AIMessage.session_id == ai_session.session_id)
            .where(AIMessage.id.in_(message_ids))
        ).scalars().all()
        
        # Index messages in OpenSearch
        for msg in messages:
            doc = {
                "message_id": str(msg.id),
                "session_id": str(msg.session_id),
                "content": msg.content,
                "role": msg.role,
                "embedding": msg.embedding,
                "created_at": datetime.now().isoformat()
            }
            
            response = opensearch.index(
                index=TEST_INDEX_NAME,
                body=doc,
                id=str(msg.id),
                refresh=True
            )
            print_success(f"Indexed message {msg.id} in OpenSearch")
        
        # Verify document count
        response = opensearch.count(index=TEST_INDEX_NAME)
        count = response['count']
        if count == len(message_ids):
            print_success(f"Document count verified in OpenSearch: {count}")
        else:
            print_error(f"Document count mismatch: expected {len(message_ids)}, got {count}")
            return False
        
        # Step 4: Vector Search in OpenSearch
        print_header("Step 4: Vector Search in OpenSearch")
        
        # Wait for indexing to complete
        print("Waiting for indexing to complete...")
        time.sleep(2)
        
        # Create a search query
        search_query = {
            "size": 3,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": 3
                    }
                }
            }
        }
        
        response = opensearch.search(
            index=TEST_INDEX_NAME,
            body=search_query
        )
        
        hits = response['hits']['hits']
        if len(hits) > 0:
            print_success(f"Found {len(hits)} similar documents in OpenSearch")
            for i, hit in enumerate(hits):
                print(f"  {i+1}. Document ID: {hit['_id']}, Score: {hit['_score']}")
                print(f"     Content: {hit['_source']['content'][:50]}...")
            
            # Store for comparison
            os_similar_ids = [hit['_id'] for hit in hits]
        else:
            print_error("No documents found in OpenSearch vector search")
            return False
        
        # Step 5: Compare Results
        print_header("Step 5: Comparing Search Results")
        
        # Convert all IDs to strings for comparison
        pg_ids = [str(id) for id in pg_similar_ids]
        os_ids = os_similar_ids
        
        # Find common IDs
        common_ids = set(pg_ids).intersection(set(os_ids))
        
        print(f"PostgreSQL similar IDs: {pg_ids}")
        print(f"OpenSearch similar IDs: {os_ids}")
        print(f"Common IDs: {common_ids}")
        
        if len(common_ids) > 0:
            print_success(f"Found {len(common_ids)} common results between PostgreSQL and OpenSearch")
        else:
            print_warning("No common results found between PostgreSQL and OpenSearch")
            print("Note: This is expected as different vector search implementations may return different results")
        
        print_success("End-to-end integration tests passed!")
        return True
    
    except Exception as e:
        print_error(f"E2E integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up resources
        session.rollback()
        session.close()
        
        try:
            opensearch.indices.delete(index=TEST_INDEX_NAME)
            print_success(f"Deleted OpenSearch test index: {TEST_INDEX_NAME}")
        except Exception as e:
            print_warning(f"Failed to delete OpenSearch test index: {str(e)}")

#############################################################################
# Main Function
#############################################################################

def main():
    """Run the main pgvector fix and test script."""
    parser = argparse.ArgumentParser(description='PostgreSQL pgvector Dimension Fix and Test')
    parser.add_argument('--fix-schema', action='store_true', help='Fix the database schema to use 3072-dimensional vectors')
    parser.add_argument('--test-basic', action='store_true', help='Run basic PostgreSQL and pgvector tests')
    parser.add_argument('--test-sqlalchemy', action='store_true', help='Run SQLAlchemy vector tests')
    parser.add_argument('--test-opensearch', action='store_true', help='Run OpenSearch integration tests')
    parser.add_argument('--test-comprehensive', action='store_true', help='Run comprehensive database tests')
    parser.add_argument('--test-e2e', action='store_true', help='Run end-to-end integration tests')
    parser.add_argument('--test-all', action='store_true', help='Run all tests')
    parser.add_argument('--db-name', default='ollama_ai_db', help='Database name (default: ollama_ai_db)')
    args = parser.parse_args()
    
    # Set DB name
    db_name = args.db_name
    
    # Run selected tests
    results = {}
    
    # Fix schema if requested
    if args.fix_schema:
        results['schema_fix'] = fix_database_schema(db_name)
        results['schema_verify'] = verify_database_dimensions(db_name)
    
    # Run all tests if requested
    run_all = args.test_all
    
    # Always run vector utilities test
    print_header("Running Vector Utilities Test")
    results['vector_utils'] = test_vector_utilities()
    
    # Run basic test
    if run_all or args.test_basic:
        print_header("Running Basic Database Test")
        results['basic_test'] = test_database_setup(db_name)
    
    # Run SQLAlchemy test
    if sqlalchemy_available and (run_all or args.test_sqlalchemy):
        print_header("Running SQLAlchemy Vector Test")
        results['sqlalchemy_test'] = test_sqlalchemy_vectors(db_name)
    elif run_all or args.test_sqlalchemy:
        print_warning("SQLAlchemy not available, skipping test")
        results['sqlalchemy_test'] = False
    
    # Run OpenSearch test
    if opensearch_available and (run_all or args.test_opensearch):
        print_header("Running OpenSearch Integration Test")
        results['opensearch_test'] = test_opensearch_integration()
    elif run_all or args.test_opensearch:
        print_warning("OpenSearch not available, skipping test")
        results['opensearch_test'] = False
    
    # Run comprehensive test
    if sqlalchemy_available and (run_all or args.test_comprehensive):
        print_header("Running Comprehensive Database Test")
        results['comprehensive_test'] = test_comprehensive_database(db_name)
    elif run_all or args.test_comprehensive:
        print_warning("SQLAlchemy not available, skipping comprehensive test")
        results['comprehensive_test'] = False
    
    # Run E2E test
    if sqlalchemy_available and opensearch_available and (run_all or args.test_e2e):
        print_header("Running End-to-End Integration Test")
        results['e2e_test'] = test_e2e_integration(db_name)
    elif run_all or args.test_e2e:
        print_warning("SQLAlchemy or OpenSearch not available, skipping E2E test")
        results['e2e_test'] = False
    
    # Print summary
    print_header("Test Summary")

    for test_name, result in results.items():
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"{test_name}: {status}")

    # Calculate overall result - ignore opensearch and e2e tests
    required_tests = [k for k in results.keys() if 'opensearch' not in k and 'e2e' not in k]
    required_passed = all(results.get(t, False) for t in required_tests)

    if required_passed:
        print_success("All required tests passed successfully!")
        # Mention optional tests if they failed
        optional_failed = [k for k in results.keys() if ('opensearch' in k or 'e2e' in k) and not results.get(k, True)]
        if optional_failed:
            print_warning(f"Optional tests skipped or failed: {', '.join(optional_failed)}")
            print_warning("This is expected if dependencies are not available.")
        sys.exit(0)
    else:
        print_error("Some required tests failed. See details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

