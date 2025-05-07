-- scripts/add_model_column_to_chat_sessions.sql

ALTER TABLE chat_sessions
ADD COLUMN model TEXT NOT NULL DEFAULT 'deepseek-coder:6.7b';
