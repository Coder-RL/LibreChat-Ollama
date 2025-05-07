--Note on pgvector dimensions:
--AI models produce 3072-dimensional vectors
--Database columns are defined as vector(3072)
--PostgreSQL internally shows this as 3068 dimensions (atttypmod-4)
--This 4-dimension offset is expected with pgvector
--Applications should always use 3072-dimensional vectors

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
    meta_data JSONB DEFAULT '{}'::jsonb,
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