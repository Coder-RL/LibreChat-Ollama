-- Create indexes for high-dimensional vectors (using appropriate index types)
BEGIN;

-- For vectors over 2000 dimensions, we need to use a non-ivfflat index type
-- For code_files table
DROP INDEX IF EXISTS idx_code_files_embedding;
CREATE INDEX idx_code_files_embedding ON code_files 
USING hnsw (embedding vector_l2_ops);

-- For ai_messages table
DROP INDEX IF EXISTS idx_ai_messages_embedding;
CREATE INDEX idx_ai_messages_embedding ON ai_messages 
USING hnsw (embedding vector_l2_ops);

-- If hnsw doesn't work (it's only available in newer pgvector versions),
-- we'll try using regular vector_ops which works with any dimensions
DO $$
BEGIN
    -- If we get here, the indexes were created successfully
    RAISE NOTICE 'Successfully created HNSW indexes';
EXCEPTION WHEN OTHERS THEN
    -- If the HNSW index creation failed, try regular vector_ops
    RAISE NOTICE 'HNSW indexes failed, trying vector_ops: %', SQLERRM;
    
    -- Drop any failed indexes if they were partially created
    EXECUTE 'DROP INDEX IF EXISTS idx_code_files_embedding';
    EXECUTE 'DROP INDEX IF EXISTS idx_ai_messages_embedding';
    
    -- Create standard vector_ops indexes (these work but are slower)
    EXECUTE 'CREATE INDEX idx_code_files_embedding ON code_files USING btree (embedding vector_ops)';
    EXECUTE 'CREATE INDEX idx_ai_messages_embedding ON ai_messages USING btree (embedding vector_ops)';
    
    RAISE NOTICE 'Created btree vector_ops indexes successfully';
END $$;

-- Verify the indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    indexname IN ('idx_code_files_embedding', 'idx_ai_messages_embedding');

COMMIT;