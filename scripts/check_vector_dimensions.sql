-- Check current vector dimensions in the database
SELECT 
    relname AS table_name, 
    attname AS column_name,
    pg_catalog.format_type(atttypid, atttypmod) AS data_type,
    atttypmod-4 AS vector_dimension  
FROM pg_attribute
JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
WHERE relname IN ('ai_messages', 'code_files', 'code_functions', 'project_files') 
  AND attname = 'embedding';