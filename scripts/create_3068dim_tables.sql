-- Create tables with explicit 3068 dimensions to match system behavior
-- Begin transaction
BEGIN;

-- Drop and recreate code_files_fixed table with explicit 3068 dimensions
DROP TABLE IF EXISTS code_files_fixed CASCADE;
CREATE TABLE code_files_fixed (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    language TEXT NOT NULL,
    file_content TEXT NOT NULL,
    embedding VECTOR(3068) NULL, -- Explicit 3068 dimensions
    ast_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TIMESTAMP WITH TIME ZONE
);

-- Drop and recreate ai_messages_fixed table with explicit 3068 dimensions
DROP TABLE IF EXISTS ai_messages_fixed CASCADE;
CREATE TABLE ai_messages_fixed (
    id SERIAL,
    session_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding VECTOR(3068) NULL, -- Explicit 3068 dimensions
    inference_id INTEGER NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (id)
);

-- Add foreign key constraint
ALTER TABLE ai_messages_fixed
ADD CONSTRAINT fk_ai_messages_fixed_session_id
FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id) ON DELETE CASCADE;

-- Check the actual dimensions of the new tables
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
    relname IN ('ai_messages_fixed', 'code_files_fixed')
    AND attname = 'embedding';

-- Test vector insertion with 3068 dimensions
DO $$
BEGIN
    -- Create test table with 3068 dimensions
    EXECUTE 'CREATE TEMP TABLE vector_test (v vector(3068))';
    
    -- Try simple vector insertion
    BEGIN
        EXECUTE 'INSERT INTO vector_test VALUES (''[0.1,0.2,0.3]'')';
        RAISE NOTICE 'Successfully inserted vector with simplified format';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Failed with simplified format: %', SQLERRM;
    END;
    
    -- Clean up
    EXECUTE 'DROP TABLE vector_test';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error in vector test: %', SQLERRM;
END;
$$;

COMMIT;