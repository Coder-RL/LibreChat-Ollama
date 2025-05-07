from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, constr
import httpx

# Import rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rag_api")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="LibreChat RAG API",
    description="Retrieval-Augmented Generation API for LibreChat-Ollama",
    version="1.0.0",
)

# Custom rate limit exceeded handler to track security events
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client_ip = request.client.host
    endpoint = request.url.path

    # Track rate limit hits in security log
    SECURITY_LOG["rate_limit_hits"][f"{client_ip}:{endpoint}"] += 1

    # Log the rate limit hit
    logger.warning(f"Rate limit exceeded for {endpoint} from {client_ip}")

    # Return standard rate limit response
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "limit": str(exc.detail)
        }
    )

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Import token store for API key validation and management
from .token_store import is_valid_token, list_tokens, prune_stale_tokens, get_token_usage_stats

# Security logging and monitoring
from collections import defaultdict
SECURITY_LOG = {
    "invalid_keys": defaultdict(int),
    "blocked_ips": defaultdict(int),
    "unknown_token_ips": defaultdict(set),
    "rate_limit_hits": defaultdict(int)
}
INVALID_THRESHOLD = int(os.getenv("INVALID_KEY_THRESHOLD", "5"))

# Optional IP whitelist (empty means allow all)
WHITELISTED_IPS = set(os.getenv("WHITELISTED_IPS", "127.0.0.1,localhost").split(","))
IP_WHITELIST_ENABLED = os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true"

# API key validation dependency
def validate_api_key(x_api_key: str = Header(..., description="API key for authentication"),
                    request: Request = None):
    """
    Validate the API key provided in the x-api-key header.
    Optionally validate client IP if IP whitelisting is enabled.
    Tracks security events like invalid keys and new IPs.
    """
    client_ip = request.client.host if request else "unknown"

    # Validate API key
    if not is_valid_token(x_api_key, client_ip):
        # Track invalid key attempts
        SECURITY_LOG["invalid_keys"][client_ip] += 1

        # Log warning or error based on threshold
        if SECURITY_LOG["invalid_keys"][client_ip] >= INVALID_THRESHOLD:
            logger.error(f"❗ SECURITY ALERT: Multiple failed auth attempts from {client_ip}")
        else:
            logger.warning(f"Invalid API key attempt from {client_ip}")

        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    # Check IP whitelist if enabled
    if IP_WHITELIST_ENABLED and request:
        if client_ip not in WHITELISTED_IPS:
            SECURITY_LOG["blocked_ips"][client_ip] += 1
            logger.warning(f"Access attempt from non-whitelisted IP: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail="Access denied from this IP address"
            )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Models
class EmbeddingRequest(BaseModel):
    text: constr(min_length=1, max_length=10000) = Field(..., description="Text to embed")

class EmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="Vector embedding of the text")
    dim: int = Field(..., description="Dimensions of the embedding vector")
    input_length: int = Field(..., description="Length of the input text")

class QueryRequest(BaseModel):
    query: constr(min_length=3, max_length=1000) = Field(..., description="Query text to search for")
    top_k: int = Field(3, ge=1, le=20, description="Number of results to return (1-20)")
    filter: Optional[Dict[str, Any]] = Field(None, description="Optional filters for the query")

class QueryResult(BaseModel):
    text: str = Field(..., description="Text content of the result")
    metadata: Dict[str, Any] = Field({}, description="Metadata associated with the result")
    score: float = Field(..., description="Similarity score")

class QueryResponse(BaseModel):
    results: List[QueryResult] = Field([], description="Search results")
    query: str = Field(..., description="Original query text")

# Health check endpoint
@app.get("/health", status_code=200)
async def health_check():
    """Health check endpoint to verify the API is running."""
    try:
        # Check if Ollama is available
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/version")
            if response.status_code != 200:
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": "Ollama service unavailable"}
                )

        # Check database connection (placeholder - implement actual check)
        # This would check PostgreSQL with pgvector

        return {"status": "healthy", "message": "RAG API is operational"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": f"Service unhealthy: {str(e)}"}
        )

# Embedding endpoint
@app.post("/embed", response_model=EmbeddingResponse, dependencies=[Depends(validate_api_key)])
@limiter.limit("10/minute")
async def create_embedding(req: EmbeddingRequest, request: Request):
    """Generate embeddings for the provided text using Ollama."""
    try:
        # Log request for monitoring
        client_ip = request.client.host
        logger.info(f"Embedding request from {client_ip} - text length: {len(req.text)}")

        # For testing purposes, generate a random embedding
        # In production, this would call Ollama's embedding API
        vector_dim = int(os.environ.get("VECTOR_DIM", 3072))
        mock_embedding = np.random.rand(vector_dim).tolist()

        return {
            "embedding": mock_embedding,
            "dim": vector_dim,
            "input_length": len(req.text)
        }
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

# RAG query endpoint
@app.post("/rag/query", response_model=QueryResponse, dependencies=[Depends(validate_api_key)])
@limiter.limit("20/minute")
async def query_rag(req: QueryRequest, request: Request):
    """Query the RAG system with the provided text."""
    try:
        # Log request for monitoring
        client_ip = request.client.host
        logger.info(f"RAG query from {client_ip} - query: '{req.query[:30]}...' top_k: {req.top_k}")

        # For testing purposes, return mock results
        # In production, this would query the pgvector database

        # Generate mock results
        mock_results = []
        for i in range(req.top_k):
            mock_results.append({
                "text": f"This is a mock result {i+1} for query: {req.query}",
                "metadata": {
                    "source": f"document_{i+1}.txt",
                    "page": i+1,
                    "timestamp": time.time()
                },
                "score": round(0.9 - (i * 0.1), 2)  # Decreasing scores
            })

        return {
            "results": mock_results,
            "query": req.query
        }
    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process RAG query: {str(e)}")

# Token usage dashboard endpoint
@app.get("/tokens/usage", dependencies=[Depends(validate_api_key)])
async def token_usage():
    """Get usage statistics for all tokens."""
    stats = get_token_usage_stats()
    return JSONResponse(content=stats)

# Token pruning endpoint
@app.post("/tokens/prune", dependencies=[Depends(validate_api_key)])
async def prune_tokens():
    """Remove tokens that haven't been used for a long time."""
    removed = prune_stale_tokens()
    return {
        "revoked": [r[0][:6] + "..." for r in removed],
        "count": len(removed),
        "details": [{"label": r[1].get("label"), "last_used": r[1].get("last_used")} for r in removed]
    }

# Security audit endpoint
@app.get("/security/audit", dependencies=[Depends(validate_api_key)])
async def security_audit():
    """Get security audit information."""
    return {
        "invalid_key_attempts": dict(SECURITY_LOG["invalid_keys"]),
        "blocked_ips": dict(SECURITY_LOG["blocked_ips"]),
        "unknown_token_ips": {k: list(v) for k, v in SECURITY_LOG["unknown_token_ips"].items()},
        "rate_limit_hits": dict(SECURITY_LOG["rate_limit_hits"])
    }

# Root endpoint with API information
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LibreChat RAG API",
        "version": "1.0.0",
        "description": "Retrieval-Augmented Generation API for LibreChat-Ollama",
        "authentication": "API key required via x-api-key header for all endpoints except /health",
        "endpoints": [
            {"path": "/health", "method": "GET", "description": "Health check endpoint", "auth_required": False},
            {"path": "/embed", "method": "POST", "description": "Generate embeddings for text", "auth_required": True},
            {"path": "/rag/query", "method": "POST", "description": "Query the RAG system", "auth_required": True},
            {"path": "/tokens/usage", "method": "GET", "description": "Get token usage statistics", "auth_required": True},
            {"path": "/tokens/prune", "method": "POST", "description": "Remove stale tokens", "auth_required": True},
            {"path": "/security/audit", "method": "GET", "description": "Get security audit information", "auth_required": True}
        ],
        "documentation": "/docs"
    }

# Run the application with: uvicorn app.main:app --host 0.0.0.0 --port 5110 --reload
