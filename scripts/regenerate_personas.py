#!/usr/bin/env python3
"""
Regenerate all persona files with the correct template tags.
"""

import os
import sys
import json
import glob

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.role_prompts import ROLE_PROMPTS
from app.services.role_inference_engine import ROLE_KEYWORDS

def generate_description(role_id):
    """
    Generate a description for a role based on its ID.
    """
    # Replace underscores with spaces and capitalize each word
    name = role_id.replace('_', ' ').title()
    
    descriptions = {
        "expert_coder_python3": "Expert Python 3 coder who writes clear, idiomatic, and production-safe code.",
        "expert_coder_flutter_and_dart": "Expert Flutter and Dart developer who creates beautiful, responsive, and maintainable mobile applications.",
        "expert_coder_kotlin": "Expert Kotlin developer who writes clean, idiomatic, and efficient code for Android and server-side applications.",
        "expert_coder_swift": "Expert Swift developer who creates elegant, performant, and maintainable iOS and macOS applications.",
        "expert_general_coder": "Versatile programming expert with knowledge across multiple languages and frameworks.",
        "refactor_engineer": "Specialist in code refactoring who improves code quality, readability, and maintainability without changing functionality.",
        "security_auditor": "Security expert who identifies and mitigates vulnerabilities in code and system design.",
        "performance_optimizer": "Performance specialist who identifies bottlenecks and optimizes code for speed, memory usage, and scalability.",
        "architect_designer": "Software architect who designs scalable, maintainable, and robust system architectures."
    }
    
    return descriptions.get(role_id, f"A persona for {name}")

def extract_keywords(role_id):
    """
    Extract keywords for a role from ROLE_KEYWORDS.
    """
    return ROLE_KEYWORDS.get(role_id, [])

def generate_tags(role_id, keywords):
    """
    Generate tags for a role based on its ID and keywords.
    """
    # Start with some basic tags from the role ID
    tags = role_id.replace('expert_', '').replace('_', ', ').split(', ')
    
    # Add some keywords as tags (limit to 5)
    for keyword in keywords[:5]:
        # Clean up the keyword (remove special chars)
        clean_keyword = keyword.replace(' ', '').strip()
        if clean_keyword and clean_keyword not in tags:
            tags.append(clean_keyword)
    
    return tags

def generate_examples(role_id, keywords):
    """
    Generate code examples for a role based on its ID and keywords.
    """
    examples = []
    
    if "python" in role_id:
        examples = [
            "def process_data(data: list) -> dict:",
            "class DataProcessor:",
            "with open('file.txt', 'r') as f:"
        ]
    elif "flutter" in role_id or "dart" in role_id:
        examples = [
            "Widget build(BuildContext context) {",
            "class MyHomePage extends StatefulWidget {",
            "final Stream<QuerySnapshot> _stream = FirebaseFirestore.instance.collection('users').snapshots();"
        ]
    elif "kotlin" in role_id:
        examples = [
            "fun processData(data: List<String>): Map<String, Int> {",
            "class DataProcessor {",
            "val result = data.filter { it.length > 3 }.map { it.uppercase() }"
        ]
    elif "swift" in role_id:
        examples = [
            "func processData(_ data: [String]) -> [String: Int] {",
            "class DataProcessor {",
            "let result = data.filter { $0.count > 3 }.map { $0.uppercased() }"
        ]
    else:
        # Generic examples
        examples = [
            "function processData(data) {",
            "class DataProcessor {",
            "const result = data.filter(item => item.length > 3).map(item => item.toUpperCase())"
        ]
    
    return examples

def main():
    """
    Regenerate all persona files with the correct template tags.
    """
    # Create the personas directory if it doesn't exist
    personas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "personas")
    os.makedirs(personas_dir, exist_ok=True)
    
    print(f"Regenerating persona files in {personas_dir}...")
    print("-" * 60)
    
    for role_id, prompt in ROLE_PROMPTS.items():
        # Get keywords for this role
        keywords = extract_keywords(role_id)
        
        # Create the persona data
        persona = {
            "id": role_id,
            "name": role_id.replace('_', ' ').title(),
            "description": generate_description(role_id),
            "system_prompt": prompt,
            "aliases": [role_id.replace('expert_', '').replace('_', ' ')],
            "keywords": keywords,
            "technologies": [kw for kw in keywords if not kw.endswith(' ')],
            "domains": generate_tags(role_id, keywords),
            "templates": {
                "default": f"<system>\n{prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a helpful, accurate, and concise response to the user's query. Include code examples where appropriate, and explain your reasoning.\n</instructions>",
                "code": f"<system>\n{prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nProvide a code solution to the user's query. Include comments to explain your code. Make sure your code is correct, efficient, and follows best practices for the language or framework being used.\n</instructions>",
                "explanation": f"<system>\n{prompt}\n</system>\n\n<context>\n{{context}}\n</context>\n\n<instructions>\nExplain the concept or technology the user is asking about. Break down complex ideas into simpler components, and provide examples to illustrate your explanation. Focus on clarity and accuracy.\n</instructions>"
            },
            "examples": generate_examples(role_id, keywords),
            "source": "auto-generated from role_prompts.py"
        }
        
        # Write the persona to a JSON file
        file_path = os.path.join(personas_dir, f"{role_id}.json")
        with open(file_path, "w") as f:
            json.dump(persona, f, indent=2)
        
        print(f"Generated {os.path.basename(file_path)}")
    
    print("-" * 60)
    print(f"Generated {len(ROLE_PROMPTS)} JSON persona files")

if __name__ == "__main__":
    main()
