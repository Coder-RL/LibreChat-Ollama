#!/usr/bin/env python3
"""
Validate persona JSON files.
"""

import os
import json
import glob

# Constants
PERSONA_DIR = "app/personas"
REQUIRED_FIELDS = ["id", "name", "description", "system_prompt", "templates"]
REQUIRED_TEMPLATES = ["default", "code", "explanation"]

def validate_persona(persona, file_path):
    """Validate a persona."""
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in persona:
            errors.append(f"Missing required field: {field}")
    
    # Check templates
    if "templates" in persona:
        templates = persona["templates"]
        
        # Check required templates
        for template_key in REQUIRED_TEMPLATES:
            if template_key not in templates:
                errors.append(f"Missing required template: {template_key}")
        
        # Check for <system> tags
        for template_key, template in templates.items():
            if "<system>" not in template:
                errors.append(f"Template '{template_key}' is missing <system> tag")
            if "</system>" not in template:
                errors.append(f"Template '{template_key}' is missing </system> tag")
            if "<s>" in template or "</s>" in template:
                errors.append(f"Template '{template_key}' contains deprecated <s> tags")
    
    return errors

def main():
    """Validate all persona JSON files."""
    # Get all persona JSON files
    json_files = glob.glob(f"{PERSONA_DIR}/*.json")
    
    print(f"Validating {len(json_files)} persona files...")
    print("-" * 60)
    
    valid_count = 0
    invalid_count = 0
    
    for file_path in sorted(json_files):
        filename = os.path.basename(file_path)
        
        try:
            # Read the JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    persona = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"❌ {filename} — Invalid JSON: {e}")
                    invalid_count += 1
                    continue
            
            # Validate the persona
            errors = validate_persona(persona, file_path)
            
            if errors:
                print(f"❌ {filename} — {len(errors)} errors:")
                for error in errors:
                    print(f"   • {error}")
                invalid_count += 1
            else:
                print(f"✅ {filename} — Valid")
                valid_count += 1
        
        except Exception as e:
            print(f"❌ {filename} — Error: {e}")
            invalid_count += 1
    
    print("-" * 60)
    print(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
    
    if invalid_count > 0:
        print("Please fix the invalid persona files.")
        return 1
    else:
        print("All persona files are valid!")
        return 0

if __name__ == "__main__":
    main()
