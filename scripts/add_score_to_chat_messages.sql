-- scripts/add_score_to_chat_messages.sql

-- Add score column to chat_messages table
ALTER TABLE chat_messages ADD COLUMN score DOUBLE PRECISION;
