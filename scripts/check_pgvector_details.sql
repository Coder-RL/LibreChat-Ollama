-- Check pgvector extension version
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Check vector type details
SELECT typname, typlen, typcategory, typispreferred
FROM pg_type WHERE typname = 'vector';

-- Check max supported vector dimension
DO $$
DECLARE
    test_dim int;
    max_dim int := 0;
BEGIN
    FOR test_dim IN SELECT generate_series(1000, 4000, 128) LOOP
        BEGIN
            EXECUTE format('CREATE TEMP TABLE vector_test_%s (v vector(%s))', test_dim, test_dim);
            max_dim := test_dim;
            EXECUTE format('DROP TABLE vector_test_%s', test_dim);
        EXCEPTION WHEN OTHERS THEN
            EXIT;
        END;
    END LOOP;
    RAISE NOTICE 'Maximum vector dimension supported: %', max_dim;
END $$;

-- Check current vector column definitions
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