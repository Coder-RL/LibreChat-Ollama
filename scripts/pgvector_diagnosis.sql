-- Comprehensive pgvector diagnosis script
-- This will check pgvector installation details, type definitions, and column state

-- Check pgvector extension version
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Check pgvector type definitions
SELECT t.typname, t.typlen, t.typbyval, t.typcategory, t.typtype, t.typispreferred
FROM pg_type t
JOIN pg_namespace n ON t.typnamespace = n.oid
WHERE t.typname = 'vector';

-- Check if tables use the vector type and their current dimensions
SELECT 
    c.relname AS table_name, 
    a.attname AS column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod) AS declared_type,
    a.atttypmod-4 AS internal_dimension
FROM pg_attribute a 
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_type t ON a.atttypid = t.oid
WHERE t.typname = 'vector'
AND n.nspname = 'public';

-- Check if tables are partitioned
SELECT 
    nmsp_parent.nspname AS parent_schema, 
    parent.relname AS parent_table, 
    nmsp_child.nspname AS child_schema, 
    child.relname AS child_table
FROM 
    pg_inherits
JOIN 
    pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN 
    pg_class child ON pg_inherits.inhrelid = child.oid
JOIN 
    pg_namespace nmsp_parent ON nmsp_parent.oid = parent.relnamespace
JOIN 
    pg_namespace nmsp_child ON nmsp_child.oid = child.relnamespace
WHERE 
    parent.relname IN ('ai_messages', 'code_files');

-- Test vector creation with 3072 dimensions
DO $$
BEGIN
    BEGIN
        EXECUTE 'CREATE TEMP TABLE vector_test (v vector(3072))';
        RAISE NOTICE 'Successfully created test table with vector(3072)';
        
        -- Check the actual dimension in metadata
        PERFORM attname, pg_catalog.format_type(atttypid, atttypmod) AS data_type, atttypmod-4 AS vector_dimension
        FROM pg_attribute
        JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
        WHERE relname = 'vector_test' AND attname = 'v';
        
        -- Try to insert a vector (different syntaxes)
        BEGIN
            EXECUTE 'INSERT INTO vector_test VALUES (''[1,2,3]''::vector(3072))';
            RAISE NOTICE 'Successfully inserted vector using [1,2,3]::vector(3072) syntax';
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Failed to insert using [1,2,3]::vector(3072) syntax: %', SQLERRM;
        END;
        
        DROP TABLE vector_test;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Error in vector test: %', SQLERRM;
    END;
END;
$$;