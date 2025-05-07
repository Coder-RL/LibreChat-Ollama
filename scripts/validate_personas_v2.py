#!/usr/bin/env python3
"""
Validate persona JSON files.

This script performs comprehensive validation of all persona JSON files to ensure:
- Valid JSON syntax
- Required fields (templates, default, etc.) exist
- Proper tag usage (<system>, not <s>)
- No template is accidentally empty
"""

import os
import sys
import json
import glob
from typing import List, Dict, Any

# Constants
PERSONA_DIR = "app/personas"
REQUIRED_TEMPLATE_KEYS = ["default", "code", "explanation"]
EXPECTED_TAG_START = "<system>"
EXPECTED_TAG_END = "</system>"
DEPRECATED_TAG_START = "<s>"
DEPRECATED_TAG_END = "</s>"
REQUIRED_FIELDS = ["id", "name", "description", "system_prompt", "templates"]

def validate_template(name: str, template: str) -> List[str]:
    """
    Validate a template string.
    
    Args:
        name: The name of the template
        template: The template string
        
    Returns:
        A list of validation errors
    """
    errors = []
    
    # Check if template is empty
    if not template.strip():
        errors.append(f"template '{name}' is empty")
    
    # Check for deprecated tags
    if DEPRECATED_TAG_START in template:
        errors.append(f"template '{name}' contains deprecated {DEPRECATED_TAG_START} tag")
    if DEPRECATED_TAG_END in template:
        errors.append(f"template '{name}' contains deprecated {DEPRECATED_TAG_END} tag")
    
    # Check for required tags
    if EXPECTED_TAG_START not in template:
        errors.append(f"template '{name}' is missing {EXPECTED_TAG_START} tag")
    if EXPECTED_TAG_END not in template:
        errors.append(f"template '{name}' is missing {EXPECTED_TAG_END} tag")
    
    # Check for context and instructions sections
    if "<context>" not in template:
        errors.append(f"template '{name}' is missing <context> section")
    if "</context>" not in template:
        errors.append(f"template '{name}' is missing </context> section")
    if "<instructions>" not in template:
        errors.append(f"template '{name}' is missing <instructions> section")
    if "</instructions>" not in template:
        errors.append(f"template '{name}' is missing </instructions> section")
    
    return errors

def validate_file(file_path: str) -> List[str]:
    """
    Validate a persona JSON file.
    
    Args:
        file_path: The path to the persona file
        
    Returns:
        A list of validation errors
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return [f"File does not exist: {file_path}"]
    
    # Check if file is readable
    if not os.access(file_path, os.R_OK):
        return [f"File is not readable: {file_path}"]
    
    # Parse JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except Exception as e:
        return [f"Error reading file: {e}"]
    
    errors = []
    
    # Check for required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: '{field}'")
    
    # If templates field is missing, return early
    if "templates" not in data:
        return errors
    
    # Validate templates
    templates = data["templates"]
    if not isinstance(templates, dict):
        errors.append("'templates' field must be a dictionary")
        return errors
    
    # Check for required template keys
    for key in REQUIRED_TEMPLATE_KEYS:
        if key not in templates:
            errors.append(f"missing required template: '{key}'")
        else:
            template_errors = validate_template(key, templates[key])
            errors.extend(template_errors)
    
    return errors

def main():
    """
    Validate all persona JSON files.
    """
    # Get the personas directory
    personas_dir = os.path.abspath(PERSONA_DIR)
    if not os.path.exists(personas_dir):
        print(f"❌ Error: Personas directory not found: {personas_dir}")
        sys.exit(1)
    
    # Find all JSON files in the personas directory
    json_files = glob.glob(os.path.join(personas_dir, "*.json"))
    if not json_files:
        print(f"⚠️ Warning: No JSON files found in {personas_dir}")
        sys.exit(0)
    
    print(f"🔍 Validating {len(json_files)} persona files in {personas_dir}...")
    print("-" * 80)
    
    # Track validation results
    valid_count = 0
    invalid_count = 0
    
    for file_path in sorted(json_files):
        filename = os.path.basename(file_path)
        errors = validate_file(file_path)
        
        if errors:
            invalid_count += 1
            print(f"❌ {filename} — {len(errors)} error(s):")
            for error in errors:
                print(f"   • {error}")
        else:
            valid_count += 1
            print(f"✅ {filename} — Passed all validation checks")
    
    print("-" * 80)
    
    if invalid_count == 0:
        print(f"🎉 Success! All {valid_count} persona files passed validation.")
        sys.exit(0)
    else:
        print(f"⚠️ Found {invalid_count} invalid persona files. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
