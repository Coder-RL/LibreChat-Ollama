-- scripts/add_persona_feedback_log.sql

-- Create the persona_feedback_log table to store user feedback on persona inference
CREATE TABLE IF NOT EXISTS persona_feedback_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    inferred_persona TEXT NOT NULL,
    user_score FLOAT,
    cancelled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);
