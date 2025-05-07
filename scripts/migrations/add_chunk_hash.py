"""
Migration script to add chunk_hash column to code_chunk_embeddings table
and populate it for existing records.
"""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database.session import get_db
from app.models.chunk_models import CodeChunk, CodeChunkEmbedding
from app.utils.vector_utils import compute_chunk_hash
from sqlalchemy import Column, String
from alembic import op
import sqlalchemy as sa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    """Add chunk_hash column and populate it for existing records."""
    logger.info("Starting migration to add chunk_hash column")
    
    # Add chunk_hash column
    try:
        op.add_column('code_chunk_embeddings', sa.Column('chunk_hash', sa.String(), nullable=True))
        logger.info("Added chunk_hash column")
    except Exception as e:
        logger.warning(f"Column may already exist: {e}")
    
    # Populate chunk_hash for existing records
    with get_db() as db:
        # Get all chunks and their embeddings
        chunks = db.query(CodeChunk).all()
        logger.info(f"Found {len(chunks)} code chunks to process")
        
        for chunk in chunks:
            # Compute hash for chunk content
            chunk_hash = compute_chunk_hash(chunk.content)
            
            # Update all embeddings for this chunk
            for embedding in chunk.embeddings:
                embedding.chunk_hash = chunk_hash
            
            logger.info(f"Updated hash for chunk {chunk.id}: {chunk_hash[:8]}...")
        
        # Commit changes
        db.commit()
    
    # Make chunk_hash not nullable
    try:
        op.alter_column('code_chunk_embeddings', 'chunk_hash', nullable=False)
        logger.info("Set chunk_hash to NOT NULL")
    except Exception as e:
        logger.error(f"Failed to set NOT NULL constraint: {e}")
    
    # Create index on chunk_hash
    try:
        op.create_index('idx_chunk_embeddings_chunk_hash', 'code_chunk_embeddings', ['chunk_hash'])
        logger.info("Created index on chunk_hash")
    except Exception as e:
        logger.warning(f"Index may already exist: {e}")
    
    logger.info("Migration completed successfully")

def downgrade():
    """Remove chunk_hash column."""
    logger.info("Starting downgrade to remove chunk_hash column")
    
    # Drop index
    try:
        op.drop_index('idx_chunk_embeddings_chunk_hash', table_name='code_chunk_embeddings')
        logger.info("Dropped index on chunk_hash")
    except Exception as e:
        logger.warning(f"Index may not exist: {e}")
    
    # Drop column
    try:
        op.drop_column('code_chunk_embeddings', 'chunk_hash')
        logger.info("Dropped chunk_hash column")
    except Exception as e:
        logger.error(f"Failed to drop column: {e}")
    
    logger.info("Downgrade completed")

if __name__ == "__main__":
    logger.info("Running migration script")
    upgrade()