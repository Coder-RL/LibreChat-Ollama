-- Create indexes for vector similarity search with vector(3)
BEGIN;

-- Create index for code_files
DROP INDEX IF EXISTS idx_code_files_embedding;
CREATE INDEX idx_code_files_embedding ON code_files 
USING ivfflat (embedding vector_l2_ops) WITH (lists = 10);

-- Create index for ai_messages
DROP INDEX IF EXISTS idx_ai_messages_embedding;
CREATE INDEX idx_ai_messages_embedding ON ai_messages 
USING ivfflat (embedding vector_l2_ops) WITH (lists = 10);

-- Verify indexes were created
SELECT
    tablename,
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    indexname IN ('idx_code_files_embedding', 'idx_ai_messages_embedding');

COMMIT;