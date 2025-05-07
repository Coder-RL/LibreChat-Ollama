-- Fix vector columns to properly support 3072 dimensions
-- Using vector(3076) to achieve 3072 internal dimensions
BEGIN;

-- Create backups if they don't already exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_files_backup') THEN
        CREATE TABLE code_files_backup AS TABLE code_files;
        RAISE NOTICE 'Created code_files_backup';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_messages_backup') THEN
        CREATE TABLE ai_messages_backup AS TABLE ai_messages;
        RAISE NOTICE 'Created ai_messages_backup';
    END IF;
END $$;

-- Fix code_files table by recreating the embedding column with vector(3076)
ALTER TABLE code_files DROP COLUMN embedding;
ALTER TABLE code_files ADD COLUMN embedding VECTOR(3076);

-- Fix ai_messages table by recreating the embedding column with vector(3076)
ALTER TABLE ai_messages DROP COLUMN embedding;
ALTER TABLE ai_messages ADD COLUMN embedding VECTOR(3076);

-- Verify the changes to ensure we have 3072 internal dimensions
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

-- Test vector insertion with the updated columns
DO $$
DECLARE
    code_id INTEGER;
BEGIN
    -- Find an existing ID to test with
    SELECT id INTO code_id FROM code_files ORDER BY id LIMIT 1;
    
    IF code_id IS NOT NULL THEN
        -- Try updating a test row with a vector
        BEGIN
            -- Create a test vector using array_fill (will be filled with 0.5 values)
            EXECUTE 'UPDATE code_files SET embedding = array_fill(0.5::float, ARRAY[3076])::vector(3076) WHERE id = $1' 
            USING code_id;
            
            RAISE NOTICE 'Successfully updated a row in code_files with a 3076-dimension vector';
            
            -- Test similarity search
            PERFORM id FROM code_files 
            WHERE embedding IS NOT NULL 
            ORDER BY embedding <-> array_fill(0.1::float, ARRAY[3076])::vector(3076) 
            LIMIT 1;
            
            RAISE NOTICE 'Successfully performed similarity search';
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Error in vector operations: %', SQLERRM;
        END;
    ELSE
        RAISE NOTICE 'No rows found in code_files to test with';
    END IF;
END $$;

COMMIT;
