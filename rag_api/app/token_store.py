import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("rag_api.token_store")

TOKEN_FILE = os.getenv("API_KEY_FILE", "rag_api_keys.json")
STALE_SECONDS = int(os.getenv("STALE_TOKEN_DAYS", "30")) * 24 * 3600  # Default: 30 days
HASH_TOKENS = os.getenv("HASH_TOKENS", "true").lower() == "true"  # Default: true

def _hash(token: str) -> str:
    """
    Hash a token using SHA-256.

    Args:
        token (str): The token to hash

    Returns:
        str: The hashed token
    """
    return hashlib.sha256(token.encode()).hexdigest()

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

    # If token hashing is enabled, check against hashed tokens
    if HASH_TOKENS:
        token_hash = _hash(api_key)
        is_valid = token_hash in tokens
        token_key = token_hash if is_valid else None
    else:
        # Legacy mode: check against plaintext tokens
        is_valid = api_key in tokens
        token_key = api_key if is_valid else None

    if is_valid and token_key:
        # Check if token has expired
        if "expires" in tokens[token_key] and tokens[token_key]["expires"] is not None:
            if _now() > tokens[token_key]["expires"]:
                logger.warning(f"Token has expired: {token_key[:6]}...")
                return False

        # Update token metadata
        tokens[token_key]["last_used"] = _now()
        tokens[token_key]["request_count"] = tokens[token_key].get("request_count", 0) + 1

        # Track client IP if provided
        if client_ip:
            if "seen_ips" not in tokens[token_key]:
                tokens[token_key]["seen_ips"] = []

            if client_ip not in tokens[token_key]["seen_ips"]:
                tokens[token_key]["seen_ips"].append(client_ip)
                logger.info(f"Token {token_key[:6]}... used from new IP: {client_ip}")

        save_tokens(tokens)
    else:
        # Log attempt with partial key for security
        masked_key = api_key[:3] + "..." + api_key[-3:] if len(api_key) > 6 else "***"
        logger.warning(f"Invalid token attempt: {masked_key}")

    return is_valid

def add_token(token: str, label: str = "default", ttl_seconds: Optional[int] = None) -> str:
    """
    Add a new token to the token store.

    Args:
        token (str): The token to add
        label (str): A label for the token (e.g., "admin", "read-only")
        ttl_seconds (int, optional): Time-to-live in seconds for the token

    Returns:
        str: The token that was added (for display to admin only)
    """
    if not token:
        logger.error("Cannot add empty token")
        return token

    tokens = load_tokens()

    # Calculate expiry time if TTL is provided
    now = _now()
    expires = now + ttl_seconds if ttl_seconds else None

    # Create token metadata
    token_metadata = {
        "label": label,
        "created": now,
        "last_used": None,
        "seen_ips": [],
        "request_count": 0
    }

    # Add expiry if TTL is provided
    if expires:
        token_metadata["expires"] = expires

    # Store token (hashed or plaintext)
    if HASH_TOKENS:
        token_key = _hash(token)
        tokens[token_key] = token_metadata
    else:
        tokens[token] = token_metadata

    save_tokens(tokens)

    # Log with expiry information if applicable
    if expires:
        expiry_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires))
        logger.info(f"Added token with label '{label}' (expires: {expiry_date})")
    else:
        logger.info(f"Added token with label '{label}' (no expiry)")

    return token

def revoke_token(token: str) -> bool:
    """
    Revoke (remove) a token from the token store.

    Args:
        token (str): The token to revoke

    Returns:
        bool: True if the token was revoked, False otherwise
    """
    tokens = load_tokens()

    # Check if we need to hash the token
    if HASH_TOKENS:
        token_key = _hash(token)
    else:
        token_key = token

    if token_key in tokens:
        token_info = tokens[token_key]
        del tokens[token_key]
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

def prune_stale_tokens() -> List[Tuple[str, dict]]:
    """
    Remove tokens that haven't been used for a long time or have expired.

    Returns:
        List[Tuple[str, dict]]: List of (token, metadata) pairs that were revoked
    """
    now = _now()
    tokens = load_tokens()
    revoked = []

    for token_key, metadata in list(tokens.items()):
        # Check for expired tokens
        if "expires" in metadata and metadata["expires"] is not None:
            if now > metadata["expires"]:
                revoked.append((token_key, metadata))
                del tokens[token_key]
                expiry_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metadata["expires"]))
                logger.info(f"Pruned expired token with label '{metadata.get('label', 'unknown')}' (expired: {expiry_date})")
                continue

        # Check for stale tokens
        last_used = metadata.get("last_used")
        if last_used and (now - last_used > STALE_SECONDS):
            revoked.append((token_key, metadata))
            del tokens[token_key]
            last_used_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_used))
            logger.info(f"Pruned stale token with label '{metadata.get('label', 'unknown')}' (last used: {last_used_date})")

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
        "expired_tokens": 0,
        "expiring_soon_tokens": 0,  # Tokens expiring in the next 7 days
        "tokens": {}
    }

    now = _now()

    for token_key, metadata in tokens.items():
        # Create a safe version of the token for display
        token_display = token_key[:6] + "..." + token_key[-4:] if len(token_key) > 10 else token_key

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

        # Add expiry information
        expires = metadata.get("expires")
        if expires:
            if now > expires:
                token_stats["status"] = "expired"
                stats["expired_tokens"] += 1
            else:
                days_until_expiry = round((expires - now) / 86400, 1)
                token_stats["days_until_expiry"] = days_until_expiry

                if days_until_expiry <= 7:
                    token_stats["status"] = "expiring_soon"
                    stats["expiring_soon_tokens"] += 1
                else:
                    token_stats["status"] = "active"
        else:
            token_stats["days_until_expiry"] = None
            token_stats["status"] = "active" if last_used else "unused"

        token_stats["unique_ips"] = len(metadata.get("seen_ips", []))
        token_stats["request_count"] = metadata.get("request_count", 0)
        stats["tokens"][token_display] = token_stats

    return stats
