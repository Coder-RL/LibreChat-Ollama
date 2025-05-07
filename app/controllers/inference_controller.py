"""
InferenceController for generating responses with intelligent context injection.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional

from app.context.role_context_injector import RoleAwareContextInjector
from app.context.context_formatter import ContextFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InferenceController:
    """
    Controller for generating responses with intelligent context injection.
    """
    
    def __init__(self, model: str = "codellama:13b"):
        """
        Initialize the inference controller.
        
        Args:
            model: The model to use for inference
        """
        self.model = model
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.endpoint = f"{self.base_url}/api/generate"
        self.context_formatter = ContextFormatter()
        logger.info(f"Initialized InferenceController with model={model}")
    
    def generate_response(self, prompt: str, session_id: str, project_id: str, 
                         role: str = "default", temperature: float = 0.7, 
                         max_tokens: int = 1000) -> Dict[str, Any]:
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
            # Create a role-aware context injector
            injector = RoleAwareContextInjector(role=role)
            
            # Inject relevant code chunks
            chunks = injector.inject(
                query=prompt,
                session_id=session_id,
                project_id=project_id,
                max_chunks=10
            )
            
            # Create a prompt with context
            prompt_with_context = self.context_formatter.create_prompt_with_context(
                prompt=prompt,
                chunks=chunks,
                include_metadata=True
            )
            
            # Call the Ollama API
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt_with_context,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama API: {response.status_code} - {response.text}")
                return {
                    "error": f"Error generating response: {response.status_code}",
                    "status": "error"
                }
            
            data = response.json()
            generated_text = data.get("response", "").strip()
            
            # Return the response with metadata
            result = {
                "response": generated_text,
                "status": "success",
                "metadata": {
                    "model": self.model,
                    "role": role,
                    "chunks_used": len(chunks),
                    "context_length": len(prompt_with_context),
                    "response_length": len(generated_text)
                }
            }
            
            logger.info(f"Generated response of length {len(generated_text)}")
            return result
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "error": f"Error generating response: {str(e)}",
                "status": "error"
            }
