-- First, create the update_timestamp() function if it doesn't exist
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF row(NEW.*) IS DISTINCT FROM row(OLD.*) THEN
        NEW.updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create vector indexes using HNSW instead of ivfflat (supports more dimensions)
DROP INDEX IF EXISTS idx_code_files_embedding;
DROP INDEX IF EXISTS idx_code_functions_embedding;

-- Create standard btree indexes for embedding columns as a fallback
CREATE INDEX IF NOT EXISTS idx_code_files_embedding ON code_files USING btree ((embedding[1:5]));
CREATE INDEX IF NOT EXISTS idx_code_functions_embedding ON code_functions USING btree ((embedding[1:5]));

-- Create triggers for auto-updating timestamps
CREATE TRIGGER update_code_repositories_timestamp
BEFORE UPDATE ON code_repositories
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_code_files_timestamp
BEFORE UPDATE ON code_files
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_code_functions_timestamp
BEFORE UPDATE ON code_functions
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_code_issues_timestamp
BEFORE UPDATE ON code_issues
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
