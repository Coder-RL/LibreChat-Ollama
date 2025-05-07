-- Vector type doesn't support subscripting, so let's try a different approach
-- Drop any existing indexes
DROP INDEX IF EXISTS idx_code_files_embedding;
DROP INDEX IF EXISTS idx_code_functions_embedding;

-- For pgvector, we can use the vector_ops index operator class for exact L2 distance searches
-- Create indexes using the generic vector_ops (no special index type)
CREATE INDEX IF NOT EXISTS idx_code_files_embedding ON code_files USING btree (embedding vector_ops);
CREATE INDEX IF NOT EXISTS idx_code_functions_embedding ON code_functions USING btree (embedding vector_ops);

-- Alternative: Try creating GiST indexes instead of btree for vectors if the above fails
-- CREATE INDEX IF NOT EXISTS idx_code_files_embedding ON code_files USING gist (embedding);
-- CREATE INDEX IF NOT EXISTS idx_code_functions_embedding ON code_functions USING gist (embedding);
