#!/usr/bin/env python3
"""
Fix persona template tags.

This script automatically fixes persona JSON files by:
- Replacing <s> tags with <system> tags
- Ensuring all required templates exist
- Validating JSON structure
"""

import os
import sys
import json
import glob
import argparse
from typing import Dict, Any, Tuple, List

# Constants
PERSONA_DIR = "app/personas"
REQUIRED_TEMPLATE_KEYS = ["default", "code", "explanation"]
OLD_OPEN_TAG = "<s>"
OLD_CLOSE_TAG = "</s>"
NEW_OPEN_TAG = "<system>"
NEW_CLOSE_TAG = "</system>"

def fix_template_text(text: str) -> Tuple[str, bool]:
    """
    Fix template text by replacing old tags with new tags.
    
    Args:
        text: The template text to fix
        
    Returns:
        A tuple of (fixed_text, was_modified)
    """
    modified = False
    
    # Replace old tags with new tags
    if OLD_OPEN_TAG in text:
        text = text.replace(OLD_OPEN_TAG, NEW_OPEN_TAG)
        modified = True
    
    if OLD_CLOSE_TAG in text:
        text = text.replace(OLD_CLOSE_TAG, NEW_CLOSE_TAG)
        modified = True
    
    return text, modified

def fix_file(file_path: str, dry_run: bool = False) -> Tuple[bool, List[str]]:
    """
    Fix a persona JSON file.
    
    Args:
        file_path: The path to the persona file
        dry_run: If True, don't actually write changes
        
    Returns:
        A tuple of (success, list of changes)
    """
    changes = []
    
    try:
        # Read the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                return False, [f"Invalid JSON: {e}"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    # Check if templates exist
    if "templates" not in data:
        return False, ["No 'templates' section found"]
    
    # Fix templates
    templates = data["templates"]
    if not isinstance(templates, dict):
        return False, ["'templates' is not a dictionary"]
    
    modified = False
    
    # Fix each template
    for key in list(templates.keys()):
        if isinstance(templates[key], str):
            fixed_template, was_modified = fix_template_text(templates[key])
            if was_modified:
                if not dry_run:
                    templates[key] = fixed_template
                modified = True
                changes.append(f"Fixed {OLD_OPEN_TAG}/{OLD_CLOSE_TAG} tags in template '{key}'")
    
    # Add missing templates
    for key in REQUIRED_TEMPLATE_KEYS:
        if key not in templates:
            if not dry_run:
                # Create a basic template based on the default template
                if "default" in templates and isinstance(templates["default"], str):
                    templates[key] = templates["default"]
                else:
                    system_prompt = data.get("system_prompt", "You are a helpful AI assistant.")
                    templates[key] = f"{NEW_OPEN_TAG}\n{system_prompt}\n{NEW_CLOSE_TAG}\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a helpful response to the user's query.\n</instructions>"
            modified = True
            changes.append(f"Added missing template '{key}'")
    
    # Write the changes
    if modified and not dry_run:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return False, [f"Error writing file: {e}"]
    
    return True, changes

def main():
    """
    Fix all persona JSON files.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fix persona template tags")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually write changes")
    args = parser.parse_args()
    
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
    
    print(f"🔍 {'Scanning' if args.dry_run else 'Fixing'} {len(json_files)} persona files in {personas_dir}...")
    if args.dry_run:
        print("⚠️ DRY RUN MODE: No changes will be written")
    print("-" * 80)
    
    # Track results
    success_count = 0
    error_count = 0
    modified_count = 0
    
    for file_path in sorted(json_files):
        filename = os.path.basename(file_path)
        success, changes = fix_file(file_path, args.dry_run)
        
        if not success:
            error_count += 1
            print(f"❌ {filename} — Error:")
            for change in changes:
                print(f"   • {change}")
        elif changes:
            modified_count += 1
            print(f"✅ {filename} — {'Would fix' if args.dry_run else 'Fixed'} {len(changes)} issues:")
            for change in changes:
                print(f"   • {change}")
        else:
            success_count += 1
            print(f"✓ {filename} — No changes needed")
    
    print("-" * 80)
    
    if args.dry_run:
        print(f"🔍 Dry run complete: {modified_count} files would be modified, {success_count} files already correct, {error_count} errors")
    else:
        print(f"🎉 Fix complete: {modified_count} files modified, {success_count} files already correct, {error_count} errors")
    
    if error_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
