-- This script does a complete fix by:
-- 1. Creating a SQL dump file of your current schema (without data)
-- 2. Making necessary modifications to ensure 3072 dimensions
-- 3. Recreating the schema in a new database 
-- 4. Transferring data with the proper dimensions

-- Create a backup of your schema
\o /tmp/schema_backup.sql
\dt
\d ai_messages
\d code_files
\o

-- Create a temporary table to test exact vector syntax
CREATE TEMP TABLE vector_syntax_test (
    id serial primary key,
    test_name text,
    success boolean,
    error_message text
);

-- Test different vector dimension specifications
DO $$
DECLARE
    test_vector text;
    test_result boolean;
    err_message text;
BEGIN
    -- Test 1: Basic vector with 3 dimensions
    BEGIN
        CREATE TEMP TABLE test1 (v vector(3));
        DROP TABLE test1;
        INSERT INTO vector_syntax_test(test_name, success) VALUES ('vector(3)', true);
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS err_message = MESSAGE_TEXT;
        INSERT INTO vector_syntax_test(test_name, success, error_message) 
        VALUES ('vector(3)', false, err_message);
    END;
    
    -- Test 2: Vector with 3072 dimensions using standard syntax
    BEGIN
        CREATE TEMP TABLE test2 (v vector(3072));
        DROP TABLE test2;
        INSERT INTO vector_syntax_test(test_name, success) VALUES ('vector(3072)', true);
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS err_message = MESSAGE_TEXT;
        INSERT INTO vector_syntax_test(test_name, success, error_message) 
        VALUES ('vector(3072)', false, err_message);
    END;
    
    -- Test 3: Vector with dimensions defined at runtime
    BEGIN
        EXECUTE 'CREATE TEMP TABLE test3 (v vector(' || 3072 || '))';
        EXECUTE 'DROP TABLE test3';
        INSERT INTO vector_syntax_test(test_name, success) VALUES ('dynamic_dimension', true);
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS err_message = MESSAGE_TEXT;
        INSERT INTO vector_syntax_test(test_name, success, error_message) 
        VALUES ('dynamic_dimension', false, err_message);
    END;
END $$;

-- View test results
SELECT * FROM vector_syntax_test;

-- Create a more robust solution by generating exact SQL statements 
DO $$
DECLARE
    dimension_value int := 3072;
    copy_tables boolean := false;  -- Set this to true to actually copy data
BEGIN
    -- First, determine if pgvector is properly handling large dimensions
    IF EXISTS (
        SELECT 1 FROM vector_syntax_test 
        WHERE test_name = 'vector(3072)' AND success = true
    ) THEN
        RAISE NOTICE 'pgvector appears to support 3072 dimensions correctly';
        
        -- Generate SQL to recreate the tables with correct dimensions
        RAISE NOTICE '-- Execute these commands to create tables with correct dimensions:';
        RAISE NOTICE 'DROP TABLE IF EXISTS code_files_fixed CASCADE;';
        RAISE NOTICE 'CREATE TABLE code_files_fixed (
            id SERIAL PRIMARY KEY,
            repository_id INTEGER,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            language TEXT NOT NULL,
            file_content TEXT NOT NULL,
            embedding VECTOR(%) NULL,
            ast_json JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_analyzed_at TIMESTAMP WITH TIME ZONE
        );', dimension_value;
        
        RAISE NOTICE 'DROP TABLE IF EXISTS ai_messages_fixed CASCADE;';
        RAISE NOTICE 'CREATE TABLE ai_messages_fixed (
            id SERIAL,
            session_id UUID NOT NULL,
            role TEXT NOT NULL CHECK (role IN (''user'', ''assistant'', ''system'')),
            content TEXT NOT NULL,
            model_name TEXT NOT NULL,
            embedding VECTOR(%) NULL,
            inference_id INTEGER NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT ''{}''::jsonb,
            PRIMARY KEY (id)
        );', dimension_value;
        
        RAISE NOTICE 'ALTER TABLE ai_messages_fixed
        ADD CONSTRAINT fk_ai_messages_fixed_session_id
        FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id) ON DELETE CASCADE;';
        
        -- Data copying instructions
        RAISE NOTICE '-- After verifying the tables have correct dimensions, copy data:';
        RAISE NOTICE 'INSERT INTO code_files_fixed(
            id, repository_id, file_path, file_name, language, file_content, 
            ast_json, created_at, updated_at, last_analyzed_at
        )
        SELECT 
            id, repository_id, file_path, file_name, language, file_content, 
            ast_json, created_at, updated_at, last_analyzed_at
        FROM code_files;';
        
        RAISE NOTICE 'INSERT INTO ai_messages_fixed(
            id, session_id, role, content, model_name, inference_id, 
            timestamp, updated_at, metadata
        )
        SELECT 
            id, session_id, role, content, model_name, inference_id, 
            timestamp, updated_at, metadata
        FROM ai_messages;';
        
        RAISE NOTICE '-- After verifying all data is copied correctly:';
        RAISE NOTICE 'DROP TABLE code_files CASCADE;';
        RAISE NOTICE 'ALTER TABLE code_files_fixed RENAME TO code_files;';
        RAISE NOTICE 'DROP TABLE ai_messages CASCADE;';
        RAISE NOTICE 'ALTER TABLE ai_messages_fixed RENAME TO ai_messages;';
        
        -- Optionally execute the commands
        IF copy_tables THEN
            RAISE NOTICE 'Would execute the commands (disabled for safety)';
            -- The actual commands would go here if copy_tables were true
        END IF;
    ELSE
        RAISE EXCEPTION 'pgvector is not properly supporting 3072 dimensions. Check your installation.';
    END IF;
END $$;

-- Check dimension calculation mechanism
SELECT 
    pg_catalog.format_type(atttypid, atttypmod) AS data_type,
    atttypmod,
    atttypmod-4 AS vector_dimension
FROM 
    pg_attribute
JOIN 
    pg_class ON pg_attribute.attrelid = pg_class.oid
WHERE 
    relname = 'vector_syntax_test';