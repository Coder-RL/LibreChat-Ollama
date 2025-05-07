-- Insert a sample repository if it doesn't exist
INSERT INTO code_repositories (name, description, language, repository_url)
VALUES ('Test Repository', 'Repository for testing vector operations', 'python', 'https://github.com/example/test')
ON CONFLICT (name) DO NOTHING;

-- Insert a basic code file with a simple vector
INSERT INTO code_files (
    repository_id,
    file_path,
    file_name,
    language,
    file_content,
    embedding
)
VALUES (
    (SELECT id FROM code_repositories WHERE name = 'Test Repository'),
    '/test/hello.py',
    'hello.py',
    'python',
    'print("Hello, world!")',
    '[0.1, 0.2, 0.3]'  -- Now matches the 3 dimensions
);

-- Add a function to the code file
INSERT INTO code_functions (
    file_id,
    function_name,
    signature,
    body,
    line_start,
    line_end,
    complexity_score,
    embedding
)
VALUES (
    (SELECT id FROM code_files WHERE file_name = 'hello.py' ORDER BY id DESC LIMIT 1),
    'main',
    'main()',
    'print("Hello, world!")',
    1,
    1,
    1.0,
    '[0.4, 0.5, 0.6]'
);
