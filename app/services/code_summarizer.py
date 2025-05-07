"""
CodeSummarizer for generating summaries of code chunks.
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeSummarizer:
    """
    Service for generating summaries of code chunks.
    """
    
    def __init__(self, model: str = "codellama:7b"):
        """
        Initialize the code summarizer.
        
        Args:
            model: The model to use for summarization
        """
        self.model = model
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.endpoint = f"{self.base_url}/api/generate"
        logger.info(f"Initialized CodeSummarizer with model={model}")
    
    def summarize(self, code: str, max_length: int = 200) -> str:
        """
        Generate a summary of the given code.
        
        Args:
            code: The code to summarize
            max_length: The maximum length of the summary
            
        Returns:
            A summary of the code
        """
        if not code or not code.strip():
            logger.warning("Empty code provided for summarization")
            return ""
        
        try:
            # Create a prompt for code summarization
            prompt = f"""
Summarize the following code concisely in one paragraph:

```
{code}
```

Summary:
"""
            
            # Call the Ollama API
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "max_tokens": max_length
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama API: {response.status_code} - {response.text}")
                return f"Error summarizing code: {response.status_code}"
            
            data = response.json()
            summary = data.get("response", "").strip()
            
            # Clean up the summary
            summary = summary.replace("Summary:", "").strip()
            
            logger.info(f"Generated summary of length {len(summary)}")
            return summary
        
        except Exception as e:
            logger.error(f"Error summarizing code: {str(e)}")
            return f"Error summarizing code: {str(e)}"
    
    def batch_summarize(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple code chunks.
        
        Args:
            chunks: List of code chunks to summarize
            
        Returns:
            The code chunks with summaries added
        """
        if not chunks:
            logger.warning("No chunks provided for summarization")
            return []
        
        try:
            for chunk in chunks:
                content = chunk.get("content", "")
                if content:
                    summary = self.summarize(content)
                    chunk["summary"] = summary
            
            logger.info(f"Generated summaries for {len(chunks)} chunks")
            return chunks
        
        except Exception as e:
            logger.error(f"Error batch summarizing chunks: {str(e)}")
            return chunks
