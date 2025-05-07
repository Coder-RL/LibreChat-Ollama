# LibreChat-Ollama RAG API

This directory contains the RAG (Retrieval-Augmented Generation) API for LibreChat-Ollama, which provides vector search capabilities using pgvector with PostgreSQL.

## Configuration

### 1. Set Up PostgreSQL with pgvector

Ensure you have PostgreSQL installed with the pgvector extension:

```bash
# Install pgvector extension in PostgreSQL
psql -U postgres -c "CREATE DATABASE ollama_ai_db;"
psql -U postgres -d ollama_ai_db -c "CREATE USER ollama_app WITH PASSWORD 'your_secure_password';"
psql -U postgres -d ollama_ai_db -c "GRANT ALL PRIVILEGES ON DATABASE ollama_ai_db TO ollama_app;"
psql -U postgres -d ollama_ai_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Secure Password Management

For security, we use `.pgpass` instead of storing passwords in environment files:

```bash
# Set up .pgpass file (recommended)
./setup_pgpass.sh your_secure_password
```

This creates a secure `.pgpass` file with the correct permissions.

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

The `.env` file is already configured to use pgvector with Ollama embeddings.

### 4. Testing the RAG API

Use the provided test script to verify the RAG API is working correctly:

```bash
# Start the RAG API
uvicorn app.main:app --host 0.0.0.0 --port 5110 --reload

# In another terminal, run the test script
./test_rag_api.sh
```

## Integration with LibreChat

The RAG API is configured in the main `librechat.yaml` file at the root of the project. Make sure the RAG API URL matches your deployment:

```yaml
rag:
  enabled: true
  vector_db: pgvector
  chunk_size: 512
  overlap: 50
  rag_api:
    base_url: "http://localhost:5110"
```

## Security Notes

- Never commit `.env` files or `librechat.yaml` with passwords to version control
- Always use `.pgpass` for PostgreSQL password management
- Keep the `.env.example` and `librechat.yaml.example` files updated for reference
