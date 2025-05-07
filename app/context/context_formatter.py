"""
ContextFormatter for formatting code chunks into a prompt.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextFormatter:
    """
    Service for formatting code chunks into a prompt.
    """
    
    def __init__(self, max_tokens: int = 8000):
        """
        Initialize the context formatter.
        
        Args:
            max_tokens: The maximum number of tokens to include in the formatted context
        """
        self.max_tokens = max_tokens
        logger.info(f"Initialized ContextFormatter with max_tokens={max_tokens}")
    
    def format_chunks(self, chunks: List[Dict[str, Any]], include_metadata: bool = True) -> str:
        """
        Format code chunks into a prompt.
        
        Args:
            chunks: The code chunks to format
            include_metadata: Whether to include metadata in the formatted context
            
        Returns:
            The formatted context
        """
        if not chunks:
            logger.warning("No chunks provided for formatting")
            return ""
        
        try:
            formatted_chunks = []
            total_tokens = 0
            
            for i, chunk in enumerate(chunks):
                # Extract chunk data
                content = chunk.get("content", "")
                file_path = chunk.get("file_path", "unknown")
                ast_type = chunk.get("ast_type", "unknown")
                score = chunk.get("score", 0.0)
                
                # Estimate token count (rough approximation)
                token_estimate = len(content.split())
                
                # Check if adding this chunk would exceed the token limit
                if total_tokens + token_estimate > self.max_tokens:
                    logger.info(f"Reached token limit after {i} chunks")
                    break
                
                # Format the chunk
                if include_metadata:
                    formatted_chunk = f"--- File: {file_path} | Type: {ast_type} | Relevance: {score:.2f} ---\n{content}\n"
                else:
                    formatted_chunk = f"--- {file_path} ---\n{content}\n"
                
                formatted_chunks.append(formatted_chunk)
                total_tokens += token_estimate
            
            # Join all formatted chunks
            formatted_context = "\n".join(formatted_chunks)
            
            logger.info(f"Formatted {len(formatted_chunks)} chunks with approximately {total_tokens} tokens")
            return formatted_context
        
        except Exception as e:
            logger.error(f"Error formatting chunks: {str(e)}")
            return ""
    
    def create_prompt_with_context(self, prompt: str, chunks: List[Dict[str, Any]], 
                                  include_metadata: bool = True) -> str:
        """
        Create a prompt with context.
        
        Args:
            prompt: The original prompt
            chunks: The code chunks to include as context
            include_metadata: Whether to include metadata in the formatted context
            
        Returns:
            The prompt with context
        """
        try:
            # Format the chunks
            formatted_context = self.format_chunks(chunks, include_metadata)
            
            if not formatted_context:
                logger.warning("No context to add to prompt")
                return prompt
            
            # Create the prompt with context
            prompt_with_context = f"""
I'll help you with your request. Here's some relevant code from the project:

{formatted_context}

Now, regarding your request:

{prompt}
"""
            
            logger.info(f"Created prompt with context (original prompt: {len(prompt)} chars, with context: {len(prompt_with_context)} chars)")
            return prompt_with_context
        
        except Exception as e:
            logger.error(f"Error creating prompt with context: {str(e)}")
            return prompt
