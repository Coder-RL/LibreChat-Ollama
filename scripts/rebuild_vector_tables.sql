-- Comprehensive table rebuild script with strict safety checks
-- This script rebuilds affected tables with proper vector dimensions

-- Begin transaction
BEGIN;

-- Safety check: ensure we can create vectors with 3072 dimensions
DO $$
DECLARE
    test_success BOOLEAN := FALSE;
BEGIN
    BEGIN
        -- Create test table
        CREATE TEMP TABLE vector_test (v vector(3072));
        
        -- Check dimension in metadata
        PERFORM 1 FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        WHERE c.relname = 'vector_test' AND a.attname = 'v' AND a.atttypmod-4 = 3072;
        
        -- If we got here, test succeeded
        test_success := TRUE;
        DROP TABLE vector_test;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Vector test failed: %', SQLERRM;
    END;
    
    -- Only proceed if test passed
    IF NOT test_success THEN
        RAISE EXCEPTION 'Cannot proceed: pgvector is not handling 3072 dimensions correctly';
    END IF;
END;
$$;

-- Create new tables with correct vector dimensions
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

-- Create a new ai_messages table (non-partitioned for now)
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
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (id)
);

-- Verify the new tables have the correct dimensions
DO $$
DECLARE
    code_files_dim INT;
    ai_messages_dim INT;
BEGIN
    SELECT atttypmod-4 INTO code_files_dim
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    WHERE c.relname = 'code_files_new' AND a.attname = 'embedding';
    
    SELECT atttypmod-4 INTO ai_messages_dim
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    WHERE c.relname = 'ai_messages_new' AND a.attname = 'embedding';
    
    IF code_files_dim = 3072 AND ai_messages_dim = 3072 THEN
        RAISE NOTICE 'New tables created with correct dimensions (3072)';
    ELSE
        RAISE EXCEPTION 'New tables have incorrect dimensions: code_files_new=%, ai_messages_new=%', 
                        code_files_dim, ai_messages_dim;
    END IF;
END;
$$;

-- Copy data from old tables to new, excluding the embedding column
INSERT INTO code_files_new(
    id, repository_id, file_path, file_name, language, file_content, 
    ast_json, created_at, updated_at, last_analyzed_at
)
SELECT 
    id, repository_id, file_path, file_name, language, file_content, 
    ast_json, created_at, updated_at, last_analyzed_at
FROM code_files;

INSERT INTO ai_messages_new(
    id, session_id, role, content, model_name, inference_id, 
    timestamp, updated_at, metadata
)
SELECT 
    id, session_id, role, content, model_name, inference_id, 
    timestamp, updated_at, metadata
FROM ai_messages;

-- Add necessary foreign key constraints
ALTER TABLE ai_messages_new
ADD CONSTRAINT fk_ai_messages_new_session_id
FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id) ON DELETE CASCADE;

-- Verify data was copied correctly
DO $$
DECLARE
    old_count INT;
    new_count INT;
BEGIN
    -- Check code_files
    SELECT COUNT(*) INTO old_count FROM code_files;
    SELECT COUNT(*) INTO new_count FROM code_files_new;
    
    IF old_count = new_count THEN
        RAISE NOTICE 'All code_files data copied successfully: % rows', new_count;
    ELSE
        RAISE EXCEPTION 'Data count mismatch for code_files: old=%, new=%', old_count, new_count;
    END IF;
    
    -- Check ai_messages
    SELECT COUNT(*) INTO old_count FROM ai_messages;
    SELECT COUNT(*) INTO new_count FROM ai_messages_new;
    
    IF old_count = new_count THEN
        RAISE NOTICE 'All ai_messages data copied successfully: % rows', new_count;
    ELSE
        RAISE EXCEPTION 'Data count mismatch for ai_messages: old=%, new=%', old_count, new_count;
    END IF;
END;
$$;

-- If everything is correct, swap the tables
DROP TABLE code_files CASCADE;
ALTER TABLE code_files_new RENAME TO code_files;

DROP TABLE ai_messages CASCADE;
ALTER TABLE ai_messages_new RENAME TO ai_messages;

-- Final verification
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

-- If we got here, everything worked
RAISE NOTICE 'Table rebuild completed successfully!';

COMMIT;