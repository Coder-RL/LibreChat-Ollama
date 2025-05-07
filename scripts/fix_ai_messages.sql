-- Begin transaction
BEGIN;

-- Create a new schema to hold our temporary tables
CREATE SCHEMA IF NOT EXISTS temp;

-- Create a new table with correct dimensions in the temp schema
CREATE TABLE temp.ai_messages (
    id SERIAL,
    session_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding VECTOR(3072) NULL,
    inference_id INTEGER NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, timestamp)
);

-- Copy the data without the embedding column (which is empty anyway according to the backup)
INSERT INTO temp.ai_messages(id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata)
SELECT id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata 
FROM ai_messages;

-- Get partition info
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

-- Now drop the original table and recreate it
DROP TABLE ai_messages CASCADE;

-- Recreate the table with the correct structure
CREATE TABLE ai_messages (
    id SERIAL,
    session_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding VECTOR(3072) NULL,
    inference_id INTEGER NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Recreate partitions
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM partition_info LOOP
        EXECUTE 'CREATE TABLE ' || r.child_name || 
                ' PARTITION OF ai_messages ' || 
                r.partition_expr;
    END LOOP;
END;
$$;

-- Copy the data back
INSERT INTO ai_messages(id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata)
SELECT id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata 
FROM temp.ai_messages;

-- Restore foreign key constraints
ALTER TABLE ai_messages 
ADD CONSTRAINT fk_ai_messages_session_id
FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id) ON DELETE CASCADE;

-- Drop temporary objects
DROP TABLE temp.ai_messages;
DROP SCHEMA temp CASCADE;

COMMIT;
BEGIN
    -- Start the table definition
    SELECT 'CREATE TABLE ' || p_schema_name || '.' || p_table_name || ' (' INTO v_table_ddl;
    
    -- Add column definitions
    FOR r IN (
        SELECT 
            a.attname AS column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
            CASE 
                WHEN a.attname = 'embedding' THEN 'VECTOR(3072)'
                ELSE pg_catalog.format_type(a.atttypid, a.atttypmod)
            END AS corrected_data_type,
            CASE WHEN a.attnotnull THEN 'NOT NULL' ELSE '' END AS not_null,
            CASE 
                WHEN a.atthasdef THEN 'DEFAULT ' || (SELECT pg_catalog.pg_get_expr(adbin, adrelid) FROM pg_catalog.pg_attrdef WHERE adrelid = a.attrelid AND adnum = a.attnum)
                ELSE ''
            END AS default_value
        FROM 
            pg_catalog.pg_attribute a
        JOIN 
            pg_catalog.pg_class c ON a.attrelid = c.oid
        JOIN 
            pg_catalog.pg_namespace n ON c.relnamespace = n.oid
        WHERE 
            n.nspname = p_schema_name
            AND c.relname = p_table_name
            AND a.attnum > 0
            AND NOT a.attisdropped
        ORDER BY 
            a.attnum
    ) LOOP
        v_table_ddl := v_table_ddl || 
                       E'\n    ' || r.column_name || ' ' || 
                       CASE WHEN r.column_name = 'embedding' THEN r.corrected_data_type ELSE r.data_type END || 
                       ' ' || r.not_null || ' ' || r.default_value || ',';
    END LOOP;
    
    -- Remove trailing comma
    v_table_ddl := substring(v_table_ddl from 1 for length(v_table_ddl) - 1);
    
    -- Close the definition
    v_table_ddl := v_table_ddl || E'\n);';
    
    RETURN v_table_ddl;
END;
$$ LANGUAGE plpgsql;

-- Get the partition info
CREATE OR REPLACE FUNCTION temp.get_partition_commands(p_parent_table VARCHAR)
RETURNS SETOF TEXT AS
$$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
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
            parent.relname = p_parent_table
    ) LOOP
        RETURN NEXT 'CREATE TABLE public.' || r.child_name || 
                    ' PARTITION OF public.ai_messages ' || 
                    r.partition_expr || ';';
    END LOOP;
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Save the table definition to a temporary table
CREATE TEMP TABLE table_definition AS 
SELECT temp.get_table_ddl('public', 'ai_messages') AS table_ddl;

-- Save the partition commands
CREATE TEMP TABLE partition_commands AS
SELECT command FROM temp.get_partition_commands('ai_messages') AS command;

-- Now drop the original table and recreate it
DROP TABLE ai_messages CASCADE;

-- Recreate the table using saved definition
DO $$
DECLARE
    v_table_ddl TEXT;
BEGIN
    SELECT table_ddl INTO v_table_ddl FROM table_definition;
    EXECUTE v_table_ddl;
END;
$$;

-- Recreate the partitions
DO $$
DECLARE
    v_command TEXT;
BEGIN
    FOR v_command IN SELECT command FROM partition_commands LOOP
        EXECUTE v_command;
    END LOOP;
END;
$$;

-- Copy the data back
INSERT INTO ai_messages(id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata)
SELECT id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata 
FROM temp.ai_messages;

-- Drop temporary objects
DROP TABLE temp.ai_messages;
DROP FUNCTION temp.get_table_ddl(VARCHAR, VARCHAR);
DROP FUNCTION temp.get_partition_commands(VARCHAR);
DROP SCHEMA temp CASCADE;

COMMIT;