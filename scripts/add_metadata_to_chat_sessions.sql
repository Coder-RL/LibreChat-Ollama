-- scripts/add_metadata_to_chat_sessions.sql

-- Add session_metadata column to chat_sessions table
ALTER TABLE chat_sessions
ADD COLUMN session_metadata JSONB;

-- Update existing sessions to have an empty metadata object
UPDATE chat_sessions
SET session_metadata = '{}'
WHERE session_metadata IS NULL;
