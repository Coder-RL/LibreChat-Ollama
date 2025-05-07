-- Check pgvector extension version and configuration
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Check if tables with vector columns exist
SELECT 
    t.table_name, 
    c.column_name, 
    c.data_type
FROM 
    information_schema.tables t
JOIN 
    information_schema.columns c ON t.table_name = c.table_name
WHERE 
    c.data_type LIKE '%vector%'
    AND t.table_schema = 'public';

-- Check current vector column definitions (actual internal dimension)
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

-- Test a simple vector operation
DO $$
BEGIN
    BEGIN
        EXECUTE 'CREATE TEMP TABLE vector_test (id serial primary key, embedding vector(3))';
        EXECUTE 'INSERT INTO vector_test (embedding) VALUES (''[1,2,3]'')';
        EXECUTE 'SELECT * FROM vector_test';
        RAISE NOTICE 'Vector operations are working correctly';
    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Vector operations failed: %', SQLERRM;
    END;
END $$;