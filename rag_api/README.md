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

The RAG API is protected by a token-based authentication system with enhanced security features. API keys are hashed using SHA-256 and stored in a JSON file with usage metadata. Tokens can be managed using the provided script:

```bash
# Generate a new token
python manage_token.py generate "admin-key" --length 32 --ttl 30d

# Add an existing token with expiry
python manage_token.py add "your-token-here" "dev-key" --ttl 7d

# List all tokens (basic view)
python manage_token.py list

# List all tokens with detailed information
python manage_token.py list --verbose

# Revoke a token
python manage_token.py revoke "token-to-revoke"

# Prune expired and stale tokens
python manage_token.py prune
```

For security, the API key is required for all endpoints except `/health`. Clients must include the API key in the `x-api-key` header for all requests.

#### Token Expiry and TTL

Tokens can be created with a time-to-live (TTL) to automatically expire after a specified period:

```bash
# Create a token that expires in 30 days
python manage_token.py generate "temp-key" --ttl 30d

# Create a token that expires in 12 hours
python manage_token.py generate "short-key" --ttl 12h

# Create a token that expires in 30 minutes
python manage_token.py generate "very-short-key" --ttl 30m
```

Expired tokens are automatically rejected and can be pruned using the `prune` command.

#### Token Usage Dashboard

The API provides a token usage dashboard to monitor token usage:

```bash
# Get token usage statistics
curl -H "x-api-key: your-token-here" http://localhost:5110/tokens/usage
```

This returns detailed information about each token, including:
- When it was created
- When it was last used
- How many requests it has made
- Which IP addresses have used it
- How many days since it was last used

#### Auto-Revoke Stale Tokens

The API can automatically revoke tokens that haven't been used for a specified period (default: 30 days):

```bash
# Prune stale tokens
curl -X POST -H "x-api-key: your-token-here" http://localhost:5110/tokens/prune
```

#### Security Audit

The API provides a security audit endpoint to monitor security events:

```bash
# Get security audit information
curl -H "x-api-key: your-token-here" http://localhost:5110/security/audit
```

This returns information about:
- Invalid API key attempts
- Blocked IP addresses
- Unknown IP addresses using tokens
- Rate limit hits

#### Prometheus Metrics

The API provides a Prometheus-compatible metrics endpoint for monitoring:

```bash
# Get metrics in Prometheus format
curl -H "x-api-key: your-token-here" http://localhost:5110/metrics
```

This returns metrics in the standard Prometheus text format:

```
# HELP ragapi_tokens_total Total number of tokens
# TYPE ragapi_tokens_total gauge
ragapi_tokens_total 5
# HELP ragapi_tokens_active Number of active tokens
# TYPE ragapi_tokens_active gauge
ragapi_tokens_active 3
# HELP ragapi_tokens_expired Number of expired tokens
# TYPE ragapi_tokens_expired gauge
ragapi_tokens_expired 1
...
```

These metrics can be scraped by Prometheus and visualized in Grafana dashboards.

#### Security Notifications

The API includes a notification script that can send alerts via email or Slack when security events occur:

```bash
# Send email notification
python notify.py email --to admin@example.com --subject "Security Alert" --message "Multiple failed auth attempts from 192.168.1.100"

# Send Slack notification
python notify.py slack --webhook https://hooks.slack.com/services/XXX/YYY/ZZZ --channel "#security" --message "Rate limit exceeded for /embed endpoint"
```

You can configure the notification settings using environment variables:

```bash
# Email settings
export SMTP_FROM="rag-api-alerts@example.com"
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="username"
export SMTP_PASSWORD="password"

# Slack settings
export SLACK_WEBHOOK="https://hooks.slack.com/services/XXX/YYY/ZZZ"
export SLACK_CHANNEL="#security-alerts"
export SLACK_USERNAME="RAG API Security Bot"
```

#### Rate Limiting

The API includes rate limiting to prevent abuse:

- `/embed` endpoint: 10 requests per minute
- `/rag/query` endpoint: 20 requests per minute

When the rate limit is exceeded, the API returns a 429 Too Many Requests response and logs the event.

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
   - Token-based authentication is implemented for all endpoints except `/health`
   - Tokens are hashed using SHA-256 to prevent plaintext storage
   - Tokens can be created with TTL for automatic expiration
   - Tokens can be rotated, revoked, and audited using the `manage_token.py` script
   - Token usage is tracked with metadata (creation time, last used, request count, IP addresses)
   - Stale tokens can be automatically revoked to prevent security risks
   - Rate limiting is implemented to prevent abuse (10/min for `/embed`, 20/min for `/rag/query`)
   - Security events are logged and can be monitored via the `/security/audit` endpoint
   - Multiple failed authentication attempts from the same IP are flagged as security alerts
   - Email and Slack notifications can be sent for security events using the `notify.py` script
   - Prometheus-compatible metrics are available for monitoring
   - In production, restrict CORS to specific origins
   - Consider using HTTPS in production environments
   - Optional IP whitelisting can be enabled for additional security

3. **Data Protection**:
   - Be aware that vector embeddings can potentially leak information
   - Consider implementing access controls for sensitive document collections
   - Regularly audit and clean up unused vector data

4. **Error Handling**:
   - The test script is designed to fail fast on errors
   - All errors are logged with detailed information
   - Never suppress or ignore security-related errors
