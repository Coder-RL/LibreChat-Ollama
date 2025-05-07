-- Begin transaction
BEGIN;

-- Fix code_files table
ALTER TABLE code_files DROP COLUMN embedding;
ALTER TABLE code_files ADD COLUMN embedding VECTOR(3072);

-- First, get a list of all existing partitions
CREATE TEMP TABLE existing_partitions AS
SELECT 
    child.relname AS partition_name
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname = 'ai_messages';

-- Create a temporary table for ai_messages with correct structure
CREATE TABLE ai_messages_new (
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

-- Create a default partition (with a different name to avoid conflicts)
CREATE TABLE ai_messages_new_default PARTITION OF ai_messages_new DEFAULT;

-- Copy data from old to new
INSERT INTO ai_messages_new(id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata)
SELECT id, session_id, role, content, model_name, inference_id, timestamp, updated_at, metadata 
FROM ai_messages;

-- Store the sequence information
DO $$
DECLARE
    seq_name TEXT;
BEGIN
    SELECT pg_get_serial_sequence('ai_messages', 'id') INTO seq_name;
    IF seq_name IS NOT NULL THEN
        EXECUTE 'ALTER SEQUENCE ' || seq_name || ' OWNED BY ai_messages_new.id';
    END IF;
END $$;

-- Drop all existing partitions first (they will be recreated)
DO $$
DECLARE
    partition_rec RECORD;
BEGIN
    FOR partition_rec IN SELECT * FROM existing_partitions LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || partition_rec.partition_name || ' CASCADE';
    END LOOP;
END $$;

-- Now drop the parent table
DROP TABLE ai_messages CASCADE;

-- Rename the new table
ALTER TABLE ai_messages_new RENAME TO ai_messages;

-- Get partition definitions
CREATE TEMP TABLE partition_definitions AS 
SELECT
    child.relname AS partition_name,
    pg_get_expr(child.relpartbound, child.oid) AS partition_expr
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
JOIN pg_namespace n ON n.oid = parent.relnamespace
WHERE parent.relname = 'ai_messages_old' 
  AND n.nspname = 'public';

-- Rename the default partition
ALTER TABLE ai_messages_new_default RENAME TO ai_messages_default;

-- Add necessary constraints
ALTER TABLE ai_messages 
ADD CONSTRAINT fk_ai_messages_session_id
FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id) ON DELETE CASCADE;

-- Create at least the basic quarterly partitions if none exist
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM existing_partitions) = 0 THEN
        -- Create specific partitions for each quarter of 2025
        EXECUTE 'CREATE TABLE ai_messages_y2025q1 PARTITION OF ai_messages
                FOR VALUES FROM (''2025-01-01'') TO (''2025-04-01'')';
                
        EXECUTE 'CREATE TABLE ai_messages_y2025q2 PARTITION OF ai_messages
                FOR VALUES FROM (''2025-04-01'') TO (''2025-07-01'')';
                
        EXECUTE 'CREATE TABLE ai_messages_y2025q3 PARTITION OF ai_messages
                FOR VALUES FROM (''2025-07-01'') TO (''2025-10-01'')';
                
        EXECUTE 'CREATE TABLE ai_messages_y2025q4 PARTITION OF ai_messages
                FOR VALUES FROM (''2025-10-01'') TO (''2026-01-01'')';
    END IF;
END $$;

COMMIT;