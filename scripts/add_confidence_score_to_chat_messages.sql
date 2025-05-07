-- Add confidence_score column to chat_messages table
ALTER TABLE chat_messages
ADD COLUMN confidence_score FLOAT;
