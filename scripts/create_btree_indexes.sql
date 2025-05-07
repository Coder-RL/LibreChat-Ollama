-- Create btree indexes for high-dimensional vectors
BEGIN;

-- Drop any existing indexes
DROP INDEX IF EXISTS idx_code_files_embedding;
DROP INDEX IF EXISTS idx_ai_messages_embedding;

-- Create standard btree indexes with vector_ops
-- These work with any dimension but are less optimized than specialized indexes
CREATE INDEX idx_code_files_embedding ON code_files USING btree (embedding vector_ops);
CREATE INDEX idx_ai_messages_embedding ON ai_messages USING btree (embedding vector_ops);

-- Verify the indexes were created
SELECT
    tablename,
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    indexname IN ('idx_code_files_embedding', 'idx_ai_messages_embedding');

COMMIT;