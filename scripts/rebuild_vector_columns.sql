-- Begin transaction
BEGIN;

-- For code_files table
ALTER TABLE code_files DROP COLUMN embedding;
ALTER TABLE code_files ADD COLUMN embedding VECTOR(3072);

-- Create a table to store information about partitions for ai_messages
CREATE TEMP TABLE partition_info AS
SELECT 
    child.relname AS child_name,
    pg_get_expr(child.relpartbound, child.oid) AS partition_expr
FROM 
    pg_inherits
JOIN 
    pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN 
    pg_class child ON pg_inherits.inhrelid = child.oid
WHERE 
    parent.relname = 'ai_messages';

-- For ai_messages table
ALTER TABLE ai_messages DROP COLUMN embedding;
ALTER TABLE ai_messages ADD COLUMN embedding VECTOR(3072);

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

-- Test if vector operations work correctly
CREATE TEMP TABLE vector_test (v VECTOR(3072));
INSERT INTO vector_test VALUES ('[0,1,2]');
SELECT array_length(v::float[], 1) FROM vector_test;
DROP TABLE vector_test;

-- Commit the changes
COMMIT;