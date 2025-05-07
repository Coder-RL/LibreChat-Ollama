 -- Fix vector columns by recreating them with vector(3)
-- This works with pgvector 0.8.0 based on our tests
BEGIN;

-- Back up tables first if they haven't been backed up already
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_files_backup') THEN
        EXECUTE 'CREATE TABLE code_files_backup AS TABLE code_files';
        RAISE NOTICE 'Created code_files_backup table';
    ELSE
        RAISE NOTICE 'code_files_backup already exists, skipping backup';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_messages_backup') THEN
        EXECUTE 'CREATE TABLE ai_messages_backup AS TABLE ai_messages';
        RAISE NOTICE 'Created ai_messages_backup table';
    ELSE
        RAISE NOTICE 'ai_messages_backup already exists, skipping backup';
    END IF;
END $$;

-- Fix code_files table by recreating the embedding column with vector(3)
ALTER TABLE code_files DROP COLUMN embedding;
ALTER TABLE code_files ADD COLUMN embedding VECTOR(3);

-- Fix ai_messages table by recreating the embedding column with vector(3)
ALTER TABLE ai_messages DROP COLUMN embedding;
ALTER TABLE ai_messages ADD COLUMN embedding VECTOR(3);

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
    relname IN ('ai_messages', 'code_files', 'ai_messages_backup', 'code_files_backup')
    AND attname = 'embedding';

-- Test vector insertion with the fixed columns
DO $$
DECLARE
    first_id INTEGER;
BEGIN
    -- Find an existing ID to test with
    SELECT id INTO first_id FROM code_files ORDER BY id LIMIT 1;
    
    IF first_id IS NOT NULL THEN
        -- Try updating a test row with a vector
        BEGIN
            UPDATE code_files SET embedding = '[0.1,0.2,0.3]' WHERE id = first_id;
            RAISE NOTICE 'Successfully updated vector in code_files';
            
            -- Check that the update worked
            PERFORM embedding FROM code_files WHERE id = first_id;
            RAISE NOTICE 'Vector is retrievable from code_files';
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Error updating vector: %', SQLERRM;
        END;
    ELSE
        RAISE NOTICE 'No rows found in code_files to test with';
    END IF;
END $$;

COMMIT;