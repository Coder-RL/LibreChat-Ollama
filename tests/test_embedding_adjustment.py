import pytest
import numpy as np
from app.services.ollama_embedding_service import OllamaEmbeddingService
from app.config.constants import VECTOR_STORAGE_DIM

@pytest.fixture(scope="module")
def embedding_service():
    return OllamaEmbeddingService()

def test_ollama_embedding_shape(embedding_service):
    text = "The quick brown fox jumps over the lazy dog."
    embedding = embedding_service.generate_embedding(text)

    assert embedding is not None, "Embedding should not be None"
    assert isinstance(embedding, np.ndarray), "Embedding should be a numpy array"
    assert embedding.shape == (VECTOR_STORAGE_DIM,), f"Expected shape ({VECTOR_STORAGE_DIM},), got {embedding.shape}"

def test_ollama_embedding_consistency(embedding_service):
    text = "Consistency check"
    vec1 = embedding_service.generate_embedding(text)
    vec2 = embedding_service.generate_embedding(text)

    assert vec1 is not None and vec2 is not None, "Embeddings should not be None"
    assert np.allclose(vec1, vec2, atol=1e-5), "Embeddings for the same input should be consistent"

def test_ollama_embedding_similarity(embedding_service):
    vec1 = embedding_service.generate_embedding("apple")
    vec2 = embedding_service.generate_embedding("banana")

    sim = embedding_service.calculate_similarity(vec1, vec2)

    assert isinstance(sim, float), "Similarity should be a float"
    assert 0.0 <= sim <= 1.0, f"Similarity out of bounds: {sim}"

def test_embedding_is_adjusted_to_3072(embedding_service):
    text = "Ensure 768D is padded to 3072D"
    embedding = embedding_service.generate_embedding(text)

    assert embedding is not None, "Embedding should not be None"
    assert isinstance(embedding, np.ndarray), "Should return a NumPy array"
    assert embedding.shape == (VECTOR_STORAGE_DIM,), f"Expected 3072D vector, got {embedding.shape}"
