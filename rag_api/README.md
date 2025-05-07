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

#### API Key Security

The RAG API is protected by an API key. You can generate a secure random API key using the provided script:

```bash
./generate_api_key.sh [key_length]
```

This will:
- Generate a cryptographically secure random API key
- Update the `.env` file with the new key
- Update the test script to use the new key

For security, the API key is required for all endpoints except `/health`. Clients must include the API key in the `x-api-key` header for all requests.

### 4. Testing the RAG API

Use the provided test script to verify the RAG API is working correctly:

```bash
# Start the RAG API
./start_api.sh

# In another terminal, run the test script
./test_rag_api.sh
```

The test script performs comprehensive validation:

- Checks if all required services (Ollama, RAG API) are running
- Validates HTTP status codes (fails on 4xx/5xx errors)
- Verifies embedding dimensions match the expected value (3072)
- Logs all requests, responses, and validation results to `rag_test.log`
- Provides detailed error messages for troubleshooting

If any test fails, the script will exit with a non-zero status code and provide detailed error information.

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

### Security Best Practices

1. **Password Management**:
   - Use `.pgpass` for PostgreSQL credentials
   - Set proper file permissions (`chmod 600 ~/.pgpass`)
   - Never store passwords in environment files or Docker Compose files

2. **API Security**:
   - API key authentication is implemented for all endpoints except `/health`
   - Use the `generate_api_key.sh` script to create strong, random API keys
   - In production, restrict CORS to specific origins
   - Add rate limiting to prevent abuse
   - Consider using HTTPS in production environments

3. **Data Protection**:
   - Be aware that vector embeddings can potentially leak information
   - Consider implementing access controls for sensitive document collections
   - Regularly audit and clean up unused vector data

4. **Error Handling**:
   - The test script is designed to fail fast on errors
   - All errors are logged with detailed information
   - Never suppress or ignore security-related errors
