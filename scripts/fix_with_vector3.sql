-- Fix vector columns by recreating them with vector(3)
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

-- Fix code_files table
ALTER TABLE code_files DROP COLUMN embedding;
ALTER TABLE code_files ADD COLUMN embedding VECTOR(3);

-- Fix ai_messages table
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
    relname IN ('ai_messages', 'code_files')
    AND attname = 'embedding';

COMMIT;