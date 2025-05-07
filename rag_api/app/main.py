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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rag_api")

# Initialize FastAPI app
app = FastAPI(
    title="LibreChat RAG API",
    description="Retrieval-Augmented Generation API for LibreChat-Ollama",
    version="1.0.0",
)

# Get API key from environment
API_KEY = os.getenv("RAG_API_KEY")
if not API_KEY:
    logger.warning("RAG_API_KEY not set in environment. API will be unsecured!")

# API key validation dependency
def validate_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """Validate the API key provided in the x-api-key header."""
    if not API_KEY:
        # If API_KEY is not set, skip validation (development only)
        logger.warning("Skipping API key validation as RAG_API_KEY is not set")
        return

    if x_api_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {x_api_key[:5]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
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
async def create_embedding(req: EmbeddingRequest):
    """Generate embeddings for the provided text using Ollama."""
    try:
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
async def query_rag(req: QueryRequest):
    """Query the RAG system with the provided text."""
    try:
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
            {"path": "/rag/query", "method": "POST", "description": "Query the RAG system", "auth_required": True}
        ],
        "documentation": "/docs"
    }

# Run the application with: uvicorn app.main:app --host 0.0.0.0 --port 5110 --reload
