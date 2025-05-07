-- Check the actual type details of vector columns
SELECT
    relname AS table_name,
    attname AS column_name,
    pg_catalog.format_type(atttypid, atttypmod) AS data_type,
    atttypmod-4 AS vector_dimension  -- PostgreSQL stores dimension as atttypmod-4
FROM
    pg_attribute
JOIN
    pg_class ON pg_attribute.attrelid = pg_class.oid
WHERE
    relname IN ('ai_messages', 'code_files')
    AND attname = 'embedding';

-- Check if pgvector extension is active and its version
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Test vector operations with correct syntax for pgvector 0.8.0
CREATE TEMP TABLE vector_test (v vector(3));
INSERT INTO vector_test VALUES ('[1,2,3]');  -- Proper syntax for pgvector 0.8.0
SELECT array_length(v::float[], 1) FROM vector_test;
DROP TABLE vector_test;