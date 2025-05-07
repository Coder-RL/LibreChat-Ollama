import os
import json
import time
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("rag_api.token_store")

TOKEN_FILE = os.getenv("API_KEY_FILE", "rag_api_keys.json")
STALE_SECONDS = int(os.getenv("STALE_TOKEN_DAYS", "30")) * 24 * 3600  # Default: 30 days

def _now() -> int:
    """Get current timestamp in seconds."""
    return int(time.time())

def load_tokens() -> Dict[str, dict]:
    """
    Load API tokens from the token file.

    Returns:
        Dict[str, dict]: Dictionary of tokens with their metadata
    """
    if not os.path.exists(TOKEN_FILE):
        logger.warning(f"Token file {TOKEN_FILE} does not exist. Creating empty token store.")
        return {}

    try:
        with open(TOKEN_FILE, "r") as f:
            tokens = json.load(f)

            # Migrate old format if needed (string labels to dict metadata)
            for token, value in list(tokens.items()):
                if isinstance(value, str):
                    tokens[token] = {
                        "label": value,
                        "created": _now(),
                        "last_used": None,
                        "seen_ips": [],
                        "request_count": 0
                    }

            return tokens
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in token file {TOKEN_FILE}")
        return {}
    except Exception as e:
        logger.error(f"Error loading tokens: {str(e)}")
        return {}

def save_tokens(tokens: Dict[str, dict]) -> None:
    """
    Save tokens to the token file.

    Args:
        tokens (Dict[str, dict]): Dictionary of tokens with their metadata
    """
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving tokens: {str(e)}")

def is_valid_token(api_key: str, client_ip: Optional[str] = None) -> bool:
    """
    Check if the provided API key is valid and update usage metadata.

    Args:
        api_key (str): The API key to validate
        client_ip (str, optional): The client IP address

    Returns:
        bool: True if the token is valid, False otherwise
    """
    if not api_key:
        return False

    tokens = load_tokens()
    is_valid = api_key in tokens

    if is_valid:
        # Update token metadata
        tokens[api_key]["last_used"] = _now()
        tokens[api_key]["request_count"] = tokens[api_key].get("request_count", 0) + 1

        # Track client IP if provided
        if client_ip:
            if "seen_ips" not in tokens[api_key]:
                tokens[api_key]["seen_ips"] = []

            if client_ip not in tokens[api_key]["seen_ips"]:
                tokens[api_key]["seen_ips"].append(client_ip)
                logger.info(f"Token {api_key[:6]}... used from new IP: {client_ip}")

        save_tokens(tokens)
    else:
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
    tokens[token] = {
        "label": label,
        "created": _now(),
        "last_used": None,
        "seen_ips": [],
        "request_count": 0
    }

    save_tokens(tokens)
    logger.info(f"Added token with label '{label}'")

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
        token_info = tokens[token]
        del tokens[token]
        save_tokens(tokens)
        logger.info(f"Revoked token with label '{token_info.get('label', 'unknown')}'")
        return True

    logger.warning(f"Attempted to revoke non-existent token")
    return False

def list_tokens() -> Dict[str, dict]:
    """
    List all tokens and their metadata.

    Returns:
        Dict[str, dict]: Dictionary of tokens with their metadata
    """
    return load_tokens()

def prune_stale_tokens() -> List[tuple]:
    """
    Remove tokens that haven't been used for a long time.

    Returns:
        List[tuple]: List of (token, metadata) pairs that were revoked
    """
    now = _now()
    tokens = load_tokens()
    revoked = []

    for token, metadata in list(tokens.items()):
        last_used = metadata.get("last_used")
        if last_used and (now - last_used > STALE_SECONDS):
            revoked.append((token, metadata))
            del tokens[token]
            logger.info(f"Pruned stale token with label '{metadata.get('label', 'unknown')}'")

    save_tokens(tokens)
    return revoked

def get_token_usage_stats() -> Dict[str, Any]:
    """
    Get usage statistics for all tokens.

    Returns:
        Dict[str, Any]: Dictionary with token usage statistics
    """
    tokens = load_tokens()
    stats = {
        "total_tokens": len(tokens),
        "active_tokens": 0,
        "unused_tokens": 0,
        "tokens": {}
    }

    now = _now()

    for token, metadata in tokens.items():
        # Create a safe version of the token for display
        token_display = token[:6] + "..." + token[-4:] if len(token) > 10 else token

        # Copy metadata but mask the full token
        token_stats = dict(metadata)

        # Add derived statistics
        last_used = metadata.get("last_used")
        if last_used:
            token_stats["days_since_last_use"] = round((now - last_used) / 86400, 1)
            stats["active_tokens"] += 1
        else:
            token_stats["days_since_last_use"] = None
            stats["unused_tokens"] += 1

        token_stats["unique_ips"] = len(metadata.get("seen_ips", []))
        stats["tokens"][token_display] = token_stats

    return stats
