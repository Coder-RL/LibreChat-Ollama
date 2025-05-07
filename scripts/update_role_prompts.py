#!/usr/bin/env python3
"""
Update role_prompts.py to only contain role names.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.role_prompts import ROLE_PROMPTS

def main():
    """
    Update role_prompts.py to only contain role names.
    """
    # Create the file content
    file_content = """# /app/config/role_prompts.py

# This file contains role prompts for the role inference engine.
# It is used by the role_inference_engine.py file.
# 
# NOTE: This file is being deprecated in favor of JSON persona files.
# The prompts have been moved to app/personas/*.json files.
# This file now only contains the role names for backward compatibility.

ROLE_PROMPTS = {
"""
    
    # Add each role with an empty prompt
    for role in ROLE_PROMPTS:
        file_content += f'    "{role}": "",\n'
    
    # Close the dictionary
    file_content += "}\n"
    
    # Write the file
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "config", "role_prompts_updated.py")
    with open(file_path, "w") as f:
        f.write(file_content)
    
    print(f"Created {file_path}")
    print("To complete the migration, rename this file to role_prompts.py")

if __name__ == "__main__":
    main()
