#!/usr/bin/env python3
"""
Token Management Script for RAG API

This script provides a command-line interface for managing API tokens
for the RAG API. It allows adding, revoking, and listing tokens.

Usage:
    python manage_token.py add [token] [label]
    python manage_token.py revoke [token]
    python manage_token.py list
    python manage_token.py generate [label] [length]
"""

import os
import sys
import json
import secrets
import string
import argparse
from app.token_store import add_token, revoke_token, list_tokens

def generate_secure_token(length=32):
    """Generate a cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def print_token_table(tokens):
    """Print tokens in a formatted table."""
    if not tokens:
        print("No tokens found.")
        return
    
    # Get the maximum length of token and label for formatting
    max_token_len = max(len(token) for token in tokens.keys())
    max_label_len = max(len(label) for label in tokens.values())
    
    # Print header
    print(f"{'Token':<{max_token_len+2}} | {'Label':<{max_label_len+2}}")
    print("-" * (max_token_len+2) + "+" + "-" * (max_label_len+4))
    
    # Print each token and label
    for token, label in tokens.items():
        print(f"{token:<{max_token_len+2}} | {label:<{max_label_len+2}}")

def main():
    parser = argparse.ArgumentParser(description="Manage RAG API tokens")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add token command
    add_parser = subparsers.add_parser("add", help="Add a new token")
    add_parser.add_argument("token", help="Token to add")
    add_parser.add_argument("label", help="Label for the token")
    
    # Generate token command
    gen_parser = subparsers.add_parser("generate", help="Generate and add a new token")
    gen_parser.add_argument("label", help="Label for the token")
    gen_parser.add_argument("--length", type=int, default=32, help="Length of the token (default: 32)")
    
    # Revoke token command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke a token")
    revoke_parser.add_argument("token", help="Token to revoke")
    
    # List tokens command
    list_parser = subparsers.add_parser("list", help="List all tokens")
    
    args = parser.parse_args()
    
    if args.command == "add":
        add_token(args.token, args.label)
        print(f"✅ Added token '{args.token}' with label '{args.label}'")
    
    elif args.command == "generate":
        token = generate_secure_token(args.length)
        add_token(token, args.label)
        print(f"✅ Generated and added new token with label '{args.label}'")
        print(f"🔑 Token: {token}")
        print("⚠️  Make sure to save this token as it won't be shown again!")
    
    elif args.command == "revoke":
        if revoke_token(args.token):
            print(f"✅ Revoked token '{args.token}'")
        else:
            print(f"❌ Token '{args.token}' not found")
    
    elif args.command == "list":
        tokens = list_tokens()
        print(f"Found {len(tokens)} tokens:")
        print_token_table(tokens)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
