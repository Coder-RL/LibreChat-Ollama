#!/usr/bin/env python3
"""
Create role_inference_patterns.py file.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.role_inference_engine import ROLE_KEYWORDS

def main():
    """
    Create role_inference_patterns.py file.
    """
    # Create the file content
    file_content = """# /app/config/role_inference_patterns.py

# This file contains patterns used for role inference.
# It is used by the role_inference_engine.py file.

ROLE_INFERENCE_PATTERNS = {
"""
    
    # Add each role and its keywords
    for role, keywords in ROLE_KEYWORDS.items():
        file_content += f'    "{role}": {keywords},\n'
    
    # Close the dictionary
    file_content += "}\n"
    
    # Write the file
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "config", "role_inference_patterns.py")
    with open(file_path, "w") as f:
        f.write(file_content)
    
    print(f"Created {file_path}")

if __name__ == "__main__":
    main()
