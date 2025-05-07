#!/usr/bin/env python3
"""
Update persona templates to use <system> tags instead of <s> tags.
"""

import os
import sys
import json
import glob

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """
    Update persona templates to use <system> tags instead of <s> tags.
    """
    # Get the personas directory
    personas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "personas")

    # Find all JSON files in the personas directory
    json_files = glob.glob(os.path.join(personas_dir, "*.json"))

    print(f"Updating {len(json_files)} persona files...")
    print("-" * 60)

    for file_path in json_files:
        # Read the JSON file
        with open(file_path, "r") as f:
            try:
                persona = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing {file_path}: {e}")
                continue

        # Update the templates
        if "templates" in persona:
            updated = False
            for template_name, template in persona["templates"].items():
                # Always update the template, regardless of whether it contains <s> or not
                updated_template = template.replace("<s>", "<system>").replace("</s>", "</system>")
                persona["templates"][template_name] = updated_template
                updated = True

            if updated:
                # Write the updated persona back to the file
                with open(file_path, "w") as f:
                    json.dump(persona, f, indent=2)
                print(f"Updated {file_path}")
            else:
                print(f"No updates needed for {file_path}")
        else:
            print(f"No templates found in {file_path}")

    print("-" * 60)
    print("Done!")

if __name__ == "__main__":
    main()
