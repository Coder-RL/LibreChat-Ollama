#!/usr/bin/env python3
"""
List all roles in ROLE_PROMPTS.
"""

import os
import sys
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.role_prompts import ROLE_PROMPTS

def main():
    """
    List all roles in ROLE_PROMPTS and their prompt lengths.
    """
    print(f"Found {len(ROLE_PROMPTS)} roles in ROLE_PROMPTS:")
    print("-" * 60)
    
    # Get the maximum role name length for pretty printing
    max_role_length = max(len(role) for role in ROLE_PROMPTS)
    
    # Print each role and its prompt length
    for role, prompt in ROLE_PROMPTS.items():
        prompt_length = len(prompt)
        print(f"{role.ljust(max_role_length)} | {prompt_length} chars")
    
    print("-" * 60)
    
    # Export roles to JSON for reference
    roles_json = {role: {"prompt_length": len(prompt)} for role, prompt in ROLE_PROMPTS.items()}
    with open("role_prompts_audit.json", "w") as f:
        json.dump(roles_json, f, indent=2)
    
    print(f"Exported roles to role_prompts_audit.json")

if __name__ == "__main__":
    main()
