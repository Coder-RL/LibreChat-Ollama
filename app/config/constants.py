"""
Constants for the LibreChat-Ollama application.
"""

# Vector storage dimension for embeddings
VECTOR_STORAGE_DIM = 3072

# Default number of chunks to retrieve
DEFAULT_CHUNK_LIMIT = 20

# Default number of chunks to include in context
DEFAULT_CONTEXT_CHUNKS = 10

# Maximum tokens for context formatting
MAX_CONTEXT_TOKENS = 8000

# Default model for code summarization
DEFAULT_SUMMARIZATION_MODEL = "codellama:7b"

# Default model for inference
DEFAULT_INFERENCE_MODEL = "codellama:13b"

# Default temperature for inference
DEFAULT_TEMPERATURE = 0.7

# Default max tokens for inference
DEFAULT_MAX_TOKENS = 1000

# Logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
