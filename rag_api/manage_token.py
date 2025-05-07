#!/usr/bin/env python3
"""
Token Management Script for RAG API

This script provides a command-line interface for managing API tokens
for the RAG API. It allows adding, revoking, and listing tokens.

Usage:
    python manage_token.py add [token] [label] [--ttl SECONDS]
    python manage_token.py revoke [token]
    python manage_token.py list [--verbose]
    python manage_token.py generate [label] [--length LENGTH] [--ttl SECONDS]
    python manage_token.py prune
"""

import os
import sys
import json
import secrets
import string
import argparse
import time
from datetime import datetime, timedelta
from app.token_store import add_token, revoke_token, list_tokens, prune_stale_tokens, _hash

def generate_secure_token(length=32):
    """Generate a cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def format_timestamp(timestamp):
    """Format a timestamp for display."""
    if timestamp is None:
        return "Never"
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def print_token_table(tokens, verbose=False):
    """Print tokens in a formatted table."""
    if not tokens:
        print("No tokens found.")
        return

    # Determine what fields to display
    if verbose:
        headers = ["Token", "Label", "Created", "Last Used", "Expires", "IPs", "Requests"]

        # Prepare rows
        rows = []
        for token_key, metadata in tokens.items():
            # For hashed tokens, show only the first 8 and last 4 characters
            token_display = token_key[:8] + "..." + token_key[-4:] if len(token_key) > 12 else token_key

            # Format timestamps
            created = format_timestamp(metadata.get("created"))
            last_used = format_timestamp(metadata.get("last_used"))
            expires = format_timestamp(metadata.get("expires"))

            # Count IPs
            ip_count = len(metadata.get("seen_ips", []))

            # Get request count
            request_count = metadata.get("request_count", 0)

            rows.append([
                token_display,
                metadata.get("label", "unknown"),
                created,
                last_used,
                expires,
                str(ip_count),
                str(request_count)
            ])

        # Calculate column widths
        col_widths = [max(len(row[i]) for row in rows + [headers]) for i in range(len(headers))]

        # Print header
        header_row = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
        print(header_row)
        print("-" * len(header_row))

        # Print rows
        for row in rows:
            print(" | ".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(headers))))
    else:
        # Simple display with just token and label
        headers = ["Token", "Label", "Status"]

        # Prepare rows
        rows = []
        now = int(time.time())
        for token_key, metadata in tokens.items():
            # For hashed tokens, show only the first 8 and last 4 characters
            token_display = token_key[:8] + "..." + token_key[-4:] if len(token_key) > 12 else token_key

            # Determine status
            status = "Active"
            if metadata.get("expires") and now > metadata.get("expires"):
                status = "Expired"
            elif metadata.get("expires") and now + (7 * 24 * 3600) > metadata.get("expires"):
                days_left = (metadata.get("expires") - now) // (24 * 3600)
                status = f"Expires in {days_left}d"
            elif not metadata.get("last_used"):
                status = "Unused"

            rows.append([token_display, metadata.get("label", "unknown"), status])

        # Calculate column widths
        col_widths = [max(len(row[i]) for row in rows + [headers]) for i in range(len(headers))]

        # Print header
        header_row = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
        print(header_row)
        print("-" * len(header_row))

        # Print rows
        for row in rows:
            print(" | ".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(headers))))

def parse_ttl(ttl_str):
    """Parse a TTL string into seconds."""
    if not ttl_str:
        return None

    # If it's just a number, assume it's seconds
    if ttl_str.isdigit():
        return int(ttl_str)

    # Parse time units (e.g., 30d, 12h, 30m)
    unit_multipliers = {
        'd': 24 * 3600,  # days
        'h': 3600,       # hours
        'm': 60,         # minutes
        's': 1           # seconds
    }

    if ttl_str[-1] in unit_multipliers:
        try:
            value = int(ttl_str[:-1])
            unit = ttl_str[-1]
            return value * unit_multipliers[unit]
        except ValueError:
            print(f"❌ Invalid TTL format: {ttl_str}")
            return None

    print(f"❌ Invalid TTL format: {ttl_str}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Manage RAG API tokens")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add token command
    add_parser = subparsers.add_parser("add", help="Add a new token")
    add_parser.add_argument("token", help="Token to add")
    add_parser.add_argument("label", help="Label for the token")
    add_parser.add_argument("--ttl", help="Time-to-live for the token (e.g., 30d, 12h, 30m, or seconds)")

    # Generate token command
    gen_parser = subparsers.add_parser("generate", help="Generate and add a new token")
    gen_parser.add_argument("label", help="Label for the token")
    gen_parser.add_argument("--length", type=int, default=32, help="Length of the token (default: 32)")
    gen_parser.add_argument("--ttl", help="Time-to-live for the token (e.g., 30d, 12h, 30m, or seconds)")

    # Revoke token command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke a token")
    revoke_parser.add_argument("token", help="Token to revoke")

    # List tokens command
    list_parser = subparsers.add_parser("list", help="List all tokens")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed token information")

    # Prune tokens command
    prune_parser = subparsers.add_parser("prune", help="Prune expired and stale tokens")

    args = parser.parse_args()

    if args.command == "add":
        ttl_seconds = parse_ttl(args.ttl)
        token = add_token(args.token, args.label, ttl_seconds)

        print(f"✅ Added token with label '{args.label}'")
        if ttl_seconds:
            expiry_date = datetime.fromtimestamp(time.time() + ttl_seconds).strftime('%Y-%m-%d %H:%M:%S')
            print(f"⏱️  Token will expire on {expiry_date}")

        # Show hash information if tokens are being hashed
        if os.environ.get("HASH_TOKENS", "true").lower() == "true":
            token_hash = _hash(args.token)
            print(f"🔒 Token hash: {token_hash}")

    elif args.command == "generate":
        ttl_seconds = parse_ttl(args.ttl)
        token = generate_secure_token(args.length)
        add_token(token, args.label, ttl_seconds)

        print(f"✅ Generated and added new token with label '{args.label}'")
        print(f"🔑 Token: {token}")
        print("⚠️  Make sure to save this token as it won't be shown again!")

        if ttl_seconds:
            expiry_date = datetime.fromtimestamp(time.time() + ttl_seconds).strftime('%Y-%m-%d %H:%M:%S')
            print(f"⏱️  Token will expire on {expiry_date}")

        # Show hash information if tokens are being hashed
        if os.environ.get("HASH_TOKENS", "true").lower() == "true":
            token_hash = _hash(token)
            print(f"🔒 Token hash: {token_hash}")

    elif args.command == "revoke":
        if revoke_token(args.token):
            print(f"✅ Revoked token")
        else:
            print(f"❌ Token not found")

    elif args.command == "list":
        tokens = list_tokens()
        print(f"Found {len(tokens)} tokens:")
        print_token_table(tokens, args.verbose)

    elif args.command == "prune":
        removed = prune_stale_tokens()
        if removed:
            print(f"✅ Pruned {len(removed)} tokens:")
            for token_key, metadata in removed:
                reason = "expired" if metadata.get("expires") and time.time() > metadata.get("expires") else "stale"
                print(f"  - {token_key[:8]}... ({metadata.get('label', 'unknown')}): {reason}")
        else:
            print("✅ No tokens to prune")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
