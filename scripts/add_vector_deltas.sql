-- scripts/add_vector_deltas.sql

-- Create the vector_deltas table to store semantic distance between original and revised responses
CREATE TABLE IF NOT EXISTS vector_deltas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_message_id UUID REFERENCES chat_messages(id),
  revised_message_id UUID REFERENCES chat_messages(id),
  similarity FLOAT,
  delta_vector VECTOR(3072),
  created_at TIMESTAMP DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_vector_deltas_original_message_id ON vector_deltas(original_message_id);
CREATE INDEX IF NOT EXISTS idx_vector_deltas_revised_message_id ON vector_deltas(revised_message_id);
CREATE INDEX IF NOT EXISTS idx_vector_deltas_similarity ON vector_deltas(similarity);

-- Add comment to the table
COMMENT ON TABLE vector_deltas IS 'Stores semantic distance between original and critique-revised responses';
