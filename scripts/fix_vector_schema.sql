-- Fix vector dimension mismatch between AI model (3072) and database (3076)
-- This script alters tables to use vector(3072) to match AI model output

-- Begin transaction
BEGIN;

-- Backup existing data with vectors (if any)
CREATE TEMP TABLE embedding_backup AS
SELECT id, embedding 
FROM ai_messages 
WHERE embedding IS NOT NULL;

-- Alter vector column in ai_messages
ALTER TABLE ai_messages ALTER COLUMN embedding TYPE vector(3072);

-- Backup data for code_files (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'code_files') THEN
        CREATE TEMP TABLE code_files_backup AS
        SELECT id, embedding 
        FROM code_files 
        WHERE embedding IS NOT NULL;
        
        -- Alter vector column in code_files
        ALTER TABLE code_files ALTER COLUMN embedding TYPE vector(3072);
    END IF;
END $$;

-- Update SQLAlchemy model in VS Code:
-- 1. Open: /Users/robertlee/GitHubProjects/ollama-inference-app/api/db/models_basic.py
-- 2. Change: embedding = Column(Vector(3076), nullable=True)
-- 3. To:     embedding = Column(Vector(3072), nullable=True)

-- Verify the changes
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