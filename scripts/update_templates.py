#!/usr/bin/env python3
"""
Update templates in persona files.
"""

import os
import json
import glob

def main():
    """
    Update templates in persona files.
    """
    # Get the personas directory
    personas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "personas")
    
    # Find all JSON files in the personas directory
    json_files = glob.glob(os.path.join(personas_dir, "*.json"))
    
    print(f"Updating templates in {len(json_files)} persona files...")
    
    for file_path in json_files:
        try:
            # Read the file content
            with open(file_path, "r") as f:
                content = f.read()
            
            # Replace <s> with <system> and </s> with </system>
            updated_content = content.replace("<s>", "<system>").replace("</s>", "</system>")
            
            # Write the updated content back to the file
            with open(file_path, "w") as f:
                f.write(updated_content)
            
            print(f"Updated {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error updating {os.path.basename(file_path)}: {e}")
    
    print("Done!")

if __name__ == "__main__":
    main()
