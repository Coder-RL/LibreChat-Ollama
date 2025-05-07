# scripts/init_database.py

import logging
from app.models.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("🔄 Initializing database...")
    db.create_tables()

    try:
        with db.engine.connect() as conn:
            from sqlalchemy import text

            # ❌ Skipping vector index creation (pgvector limit = 2000 dimensions)
            # ✅ All vector search will use OpenSearch instead

            logger.info("⚠️ Skipped vector index creation due to 3072D limit — using OpenSearch for similarity search.")

    except Exception as e:
        logger.error(f"❌ Error during database initialization: {e}")
        logger.warning("⚠️ Proceeding without vector indexes — search will rely on OpenSearch.")

    logger.info("✅ Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()

