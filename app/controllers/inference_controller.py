"""
InferenceController for generating responses with intelligent context injection.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional

from app.context.role_context_injector import RoleAwareContextInjector
from app.context.context_formatter import ContextFormatter
from app.services.embedding_service import EmbeddingService
from app.vector.chunk_retriever import ChunkRetriever
from app.context.chunk_scorer import ChunkRelevanceScorer
from app.services.code_summarizer import CodeSummarizer
from app.config.constants import VECTOR_STORAGE_DIM, DEFAULT_INFERENCE_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InferenceController:
    """
    Controller for generating responses with intelligent context injection.
    """

    def __init__(self, model: str = DEFAULT_INFERENCE_MODEL):
        """
        Initialize the inference controller.

        Args:
            model: The model to use for inference
        """
        self.model = model
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.endpoint = f"{self.base_url}/api/generate"

        # Initialize components
        self.embedding_service = EmbeddingService(dimensions=VECTOR_STORAGE_DIM)
        self.chunk_retriever = ChunkRetriever(embedding_service=self.embedding_service)
        self.chunk_scorer = ChunkRelevanceScorer(embedding_service=self.embedding_service)
        self.summarizer = CodeSummarizer()
        self.formatter = ContextFormatter()

        logger.info(f"[CTX] Initialized InferenceController with model={model}")

    def generate_response(self, prompt: str, session_id: str, project_id: str,
                         role: str = "default", temperature: float = DEFAULT_TEMPERATURE,
                         max_tokens: int = DEFAULT_MAX_TOKENS) -> Dict[str, Any]:
        """
        Generate a response with intelligent context injection.

        Args:
            prompt: The prompt to generate a response for
            session_id: The session identifier
            project_id: The project identifier
            role: The agent role
            temperature: The temperature to use for generation
            max_tokens: The maximum number of tokens to generate

        Returns:
            A dictionary containing the response and metadata
        """
        try:
            logger.info(f"[CTX] Generating response for session={session_id}, project={project_id}, role={role}")

            # Step 1: Retrieve relevant code chunks (raw)
            chunks = self.chunk_retriever.retrieve_chunks(prompt, project_id=project_id, top_k=20)

            if not chunks:
                logger.warning("[CTX] No relevant code chunks found. Returning fallback response.")
                return {
                    "response": "No relevant context found.",
                    "context": [],
                    "success": True
                }

            # Step 2: Inject context based on role (e.g., frontend, backend)
            injector = RoleAwareContextInjector(role=role, scorer=self.chunk_scorer, retriever=self.chunk_retriever)
            selected_chunks = injector.inject(prompt=prompt, project_id=project_id)

            # Step 3: Format the selected context into a prompt
            formatted_context = self.formatter.format_context(selected_chunks)

            # Step 4: Merge into final LLM prompt
            final_prompt = f"{formatted_context}\n\n{prompt}"

            # Step 5: Call the LLM
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                }
            )

            if response.status_code != 200:
                logger.error(f"[CTX] Error from Ollama API: {response.status_code} - {response.text}")
                return {
                    "response": f"Error generating response: {response.status_code}",
                    "context": [],
                    "success": False
                }

            data = response.json()
            llm_output = data.get("response", "").strip()

            logger.info(f"[CTX] LLM response generated successfully. Selected {len(selected_chunks)} chunks.")

            # Return the response with context metadata
            return {
                "response": llm_output,
                "context": [chunk for chunk in selected_chunks],
                "success": True,
                "metadata": {
                    "model": self.model,
                    "role": role,
                    "chunks_used": len(selected_chunks),
                    "context_length": len(formatted_context),
                    "response_length": len(llm_output)
                }
            }

        except Exception as e:
            logger.exception(f"[CTX] Failed to generate response: {str(e)}")
            return {
                "response": "Error occurred during inference.",
                "context": [],
                "success": False
            }
