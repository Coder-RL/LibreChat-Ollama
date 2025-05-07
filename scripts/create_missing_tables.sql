-- Create code-specific tables for enhanced analysis

-- Create code_repositories table
CREATE TABLE IF NOT EXISTS code_repositories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    language TEXT NOT NULL,
    repository_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create code_files table
CREATE TABLE IF NOT EXISTS code_files (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES code_repositories(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    language TEXT NOT NULL,
    file_content TEXT NOT NULL,
    embedding VECTOR(3072) NULL,
    ast_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TIMESTAMP WITH TIME ZONE
);

-- Create code_functions table
CREATE TABLE IF NOT EXISTS code_functions (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES code_files(id) ON DELETE CASCADE,
    function_name TEXT NOT NULL,
    signature TEXT NOT NULL,
    body TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    complexity_score FLOAT,
    embedding VECTOR(3072) NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create code_issues table
CREATE TABLE IF NOT EXISTS code_issues (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES code_files(id) ON DELETE CASCADE,
    function_id INTEGER REFERENCES code_functions(id) ON DELETE CASCADE,
    issue_type TEXT NOT NULL CHECK (issue_type IN ('bug', 'security', 'performance', 'maintainability', 'architecture')),
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    line_number INTEGER,
    description TEXT NOT NULL,
    suggestion TEXT,
    status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'wontfix', 'false_positive')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enhance AI sessions with code context (if ai_sessions table already exists)
ALTER TABLE ai_sessions 
ADD COLUMN IF NOT EXISTS current_repository_id INTEGER REFERENCES code_repositories(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS current_file_id INTEGER REFERENCES code_files(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS current_function_id INTEGER REFERENCES code_functions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS code_context JSONB DEFAULT '{}'::jsonb;

-- Create indexes for the new tables
CREATE INDEX IF NOT EXISTS idx_code_files_repository_id ON code_files(repository_id);
CREATE INDEX IF NOT EXISTS idx_code_files_language ON code_files(language);
CREATE INDEX IF NOT EXISTS idx_code_functions_file_id ON code_functions(file_id);
CREATE INDEX IF NOT EXISTS idx_code_functions_name ON code_functions(function_name);
CREATE INDEX IF NOT EXISTS idx_code_issues_file_id ON code_issues(file_id);
CREATE INDEX IF NOT EXISTS idx_code_issues_function_id ON code_issues(function_id);
CREATE INDEX IF NOT EXISTS idx_code_issues_type_severity ON code_issues(issue_type, severity);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_repository ON ai_sessions(current_repository_id) WHERE current_repository_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_sessions_file ON ai_sessions(current_file_id) WHERE current_file_id IS NOT NULL;

-- Add text search indexes for code content
CREATE INDEX IF NOT EXISTS idx_code_files_content_tsvector ON code_files USING gin(to_tsvector('english', file_content));
CREATE INDEX IF NOT EXISTS idx_code_functions_body_tsvector ON code_functions USING gin(to_tsvector('english', body));

-- Add vector index for code embeddings
CREATE INDEX IF NOT EXISTS idx_code_files_embedding ON code_files 
USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_code_functions_embedding ON code_functions 
USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);

-- Create triggers for auto-updating timestamps
-- First check if the function exists, if not create it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_timestamp') THEN
        CREATE FUNCTION update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            IF row(NEW.*) IS DISTINCT FROM row(OLD.*) THEN
                NEW.updated_at = NOW();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    END IF;
END $$;

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

-- Insert a sample repository for testing
INSERT INTO code_repositories (name, description, language, repository_url)
VALUES ('Sample Repository', 'A sample repository for testing', 'multiple', 'https://github.com/example/sample')
ON CONFLICT (name) DO NOTHING;
