import os
import json
from typing import Dict
import logging

logger = logging.getLogger("rag_api.token_store")

TOKEN_FILE = os.getenv("API_KEY_FILE", "rag_api_keys.json")

def load_tokens() -> Dict[str, str]:
    """
    Load API tokens from the token file.
    
    Returns:
        Dict[str, str]: Dictionary of tokens with their labels
    """
    if not os.path.exists(TOKEN_FILE):
        logger.warning(f"Token file {TOKEN_FILE} does not exist. Creating empty token store.")
        return {}
    
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in token file {TOKEN_FILE}")
        return {}
    except Exception as e:
        logger.error(f"Error loading tokens: {str(e)}")
        return {}

def is_valid_token(api_key: str) -> bool:
    """
    Check if the provided API key is valid.
    
    Args:
        api_key (str): The API key to validate
        
    Returns:
        bool: True if the token is valid, False otherwise
    """
    if not api_key:
        return False
    
    tokens = load_tokens()
    is_valid = api_key in tokens
    
    if not is_valid:
        # Log attempt with partial key for security
        masked_key = api_key[:3] + "..." + api_key[-3:] if len(api_key) > 6 else "***"
        logger.warning(f"Invalid token attempt: {masked_key}")
    
    return is_valid

def add_token(token: str, label: str = "default") -> None:
    """
    Add a new token to the token store.
    
    Args:
        token (str): The token to add
        label (str): A label for the token (e.g., "admin", "read-only")
    """
    if not token:
        logger.error("Cannot add empty token")
        return
    
    tokens = load_tokens()
    tokens[token] = label
    
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        logger.info(f"Added token with label '{label}'")
    except Exception as e:
        logger.error(f"Error adding token: {str(e)}")

def revoke_token(token: str) -> bool:
    """
    Revoke (remove) a token from the token store.
    
    Args:
        token (str): The token to revoke
        
    Returns:
        bool: True if the token was revoked, False otherwise
    """
    tokens = load_tokens()
    if token in tokens:
        label = tokens[token]
        del tokens[token]
        
        try:
            with open(TOKEN_FILE, "w") as f:
                json.dump(tokens, f, indent=2)
            logger.info(f"Revoked token with label '{label}'")
            return True
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    logger.warning(f"Attempted to revoke non-existent token")
    return False

def list_tokens() -> Dict[str, str]:
    """
    List all tokens and their labels.
    
    Returns:
        Dict[str, str]: Dictionary of tokens with their labels
    """
    return load_tokens()
