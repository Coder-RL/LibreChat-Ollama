#!/usr/bin/env python3
"""
Fix persona templates to use <system> tags instead of <s> tags.
"""

import os
import json
import glob

# Constants
PERSONA_DIR = "app/personas"
REQUIRED_TEMPLATES = ["default", "code", "explanation"]

def main():
    """
    Fix persona templates to use <system> tags instead of <s> tags.
    """
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
                    persona = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"❌ {filename} — Invalid JSON: {e}")
                    continue
            
            updated = False
            
            # Ensure system_prompt exists
            if "system_prompt" not in persona and "template_file" in persona:
                # Try to create a system prompt from the name and description
                name = persona.get("name", "")
                description = persona.get("description", "")
                persona["system_prompt"] = f"You are a {name}. {description}"
                updated = True
                print(f"  • Added system_prompt based on name and description")
            
            # Ensure templates exist
            if "templates" not in persona:
                system_prompt = persona.get("system_prompt", "You are a helpful AI assistant.")
                persona["templates"] = {
                    "default": f"<system>\n{system_prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a helpful, accurate, and concise response to the user's query. Include code examples where appropriate, and explain your reasoning.\n</instructions>",
                    "code": f"<system>\n{system_prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a code solution to the user's query. Include comments to explain your code. Make sure your code is correct, efficient, and follows best practices for the language or framework being used.\n</instructions>",
                    "explanation": f"<system>\n{system_prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nExplain the concept or technology the user is asking about. Break down complex ideas into simpler components, and provide examples to illustrate your explanation. Focus on clarity and accuracy.\n</instructions>"
                }
                updated = True
                print(f"  • Added missing templates")
            else:
                # Ensure all required templates exist
                templates = persona["templates"]
                system_prompt = persona.get("system_prompt", "You are a helpful AI assistant.")
                
                for template_key in REQUIRED_TEMPLATES:
                    if template_key not in templates:
                        if template_key == "default":
                            templates[template_key] = f"<system>\n{system_prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a helpful, accurate, and concise response to the user's query. Include code examples where appropriate, and explain your reasoning.\n</instructions>"
                        elif template_key == "code":
                            templates[template_key] = f"<system>\n{system_prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a code solution to the user's query. Include comments to explain your code. Make sure your code is correct, efficient, and follows best practices for the language or framework being used.\n</instructions>"
                        elif template_key == "explanation":
                            templates[template_key] = f"<system>\n{system_prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nExplain the concept or technology the user is asking about. Break down complex ideas into simpler components, and provide examples to illustrate your explanation. Focus on clarity and accuracy.\n</instructions>"
                        
                        updated = True
                        print(f"  • Added missing '{template_key}' template")
                
                # Update the templates to use <system> tags
                for template_name, template in templates.items():
                    if "<s>" in template or "</s>" in template:
                        # Replace <s> with <system> and </s> with </system>
                        new_template = template.replace("<s>", "<system>").replace("</s>", "</system>")
                        templates[template_name] = new_template
                        updated = True
                        print(f"  • Updated '{template_name}' template to use <system> tags")
            
            if updated:
                # Write the updated persona back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(persona, f, indent=2)
                
                print(f"✅ {filename} — Updated")
                fixed_count += 1
            else:
                print(f"✓ {filename} — No updates needed")
        
        except Exception as e:
            print(f"❌ {filename} — Error: {e}")
    
    print("-" * 60)
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
