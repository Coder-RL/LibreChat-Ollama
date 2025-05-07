-- Alter table columns to use vector(3072)
BEGIN;

-- Alter ai_messages table
ALTER TABLE ai_messages ALTER COLUMN embedding TYPE vector(3072);

-- Alter code_files table
ALTER TABLE code_files ALTER COLUMN embedding TYPE vector(3072);

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