#!/usr/bin/env python3
"""
Fix nested persona JSON structure.
"""

import os
import json
import glob

# Constants
PERSONA_DIR = "app/personas"

def main():
    """Fix nested persona JSON structure."""
    # Get all persona JSON files
    json_files = glob.glob(f"{PERSONA_DIR}/*.json")
    
    print(f"Fixing {len(json_files)} persona files...")
    print("-" * 60)
    
    fixed_count = 0
    
    for file_path in sorted(json_files):
        filename = os.path.basename(file_path)
        
        try:
            # Read the JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"❌ {filename} — Invalid JSON: {e}")
                    continue
            
            # Check if the data is nested under a key (usually the persona ID)
            if len(data) == 1 and isinstance(data.get(list(data.keys())[0]), dict):
                key = list(data.keys())[0]
                nested_data = data[key]
                
                # Add the ID if it's not already there
                if "id" not in nested_data:
                    nested_data["id"] = key
                
                # Write the unnested data back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(nested_data, f, indent=2)
                
                print(f"✅ {filename} — Fixed: Removed nesting under key '{key}'")
                fixed_count += 1
            else:
                print(f"✓ {filename} — No nesting issues")
        
        except Exception as e:
            print(f"❌ {filename} — Error: {e}")
    
    print("-" * 60)
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
