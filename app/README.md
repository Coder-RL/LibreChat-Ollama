# Intelligent Context Injection for LibreChat-Ollama

This module provides intelligent context injection for LibreChat-Ollama, dynamically injecting only the most relevant code chunks into the prompt based on the agent's role, file type, semantic score, and AST metadata.

## Components

### 1. RoleAwareContextInjector

The `RoleAwareContextInjector` filters and prioritizes code chunks based on the agent's role (e.g., frontend, backend, devops, security, refactor). It uses role-specific keywords and file patterns to filter chunks, ensuring that only relevant code is included in the prompt.

### 2. ChunkRelevanceScorer

The `ChunkRelevanceScorer` scores code chunks based on their relevance to the query. It combines vector similarity with AST type and file type boosting to prioritize the most relevant chunks.

### 3. ContextFormatter

The `ContextFormatter` formats the selected code chunks into a prompt, including metadata such as file path, AST type, and relevance score.

### 4. CodeSummarizer

The `CodeSummarizer` generates concise summaries of code chunks, which can be included in the prompt to provide additional context.

### 5. EmbeddingService

The `EmbeddingService` generates vector embeddings for text using Ollama's embedding API.

### 6. ChunkRetriever

The `ChunkRetriever` retrieves code chunks from vector storage based on a query.

## Usage

```python
from app.context.role_context_injector import RoleAwareContextInjector
from app.context.context_formatter import ContextFormatter

# Create a role-aware context injector
injector = RoleAwareContextInjector(role="backend")

# Inject relevant code chunks
chunks = injector.inject(
    query="How do I get a user?",
    session_id="test-session",
    project_id="test-project"
)

# Format the chunks into a prompt
formatter = ContextFormatter()
prompt_with_context = formatter.create_prompt_with_context(
    prompt="How do I get a user?",
    chunks=chunks
)

# Generate a response using the prompt with context
# ...
```

## Role-Specific Filtering

The `RoleAwareContextInjector` supports the following roles:

- **frontend**: Filters for UI components, views, HTML, CSS, etc.
- **backend**: Filters for controllers, services, models, APIs, databases, etc.
- **devops**: Filters for deployment, CI/CD, Docker, Kubernetes, etc.
- **security**: Filters for authentication, authorization, encryption, etc.
- **refactor**: Includes all chunks (no filtering)
- **default**: Includes all chunks (no filtering)

## Chunk Scoring

The `ChunkRelevanceScorer` scores chunks based on:

1. **Vector Similarity**: Cosine similarity between the query embedding and the chunk embedding
2. **AST Type Boost**: Boosts for important AST types (e.g., class, function) and penalties for less important types (e.g., import, comment)
3. **File Type Boost**: Boosts for important file types (e.g., .py, .js) and penalties for less important types (e.g., .md, .txt)

## Testing

Run the tests to verify the functionality:

```bash
python -m unittest discover tests
```

## Integration with LibreChat-Ollama

To integrate this module with LibreChat-Ollama, update the inference controller to use the `RoleAwareContextInjector`:

```python
# In inference_controller.py
from app.context.role_context_injector import RoleAwareContextInjector

# Replace this:
chunks = vector_storage.search_vectors(...)

# With this:
injector = RoleAwareContextInjector(role=session.persona_role)
chunks = injector.inject(
    query=prompt,
    session_id=session_id,
    project_id=project_id
)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
