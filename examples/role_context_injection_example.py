#!/usr/bin/env python3
"""
Example script demonstrating how to use the RoleAwareContextInjector.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.context.role_context_injector import RoleAwareContextInjector
from app.context.context_formatter import ContextFormatter
from app.controllers.inference_controller import InferenceController

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main function.
    """
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python role_context_injection_example.py <prompt> [role]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "default"
    
    # Create mock chunks for demonstration
    mock_chunks = [
        {
            "id": "1",
            "content": "def get_user(user_id):\n    return db.query(User).filter(User.id == user_id).first()",
            "file_path": "app/controllers/user_controller.py",
            "ast_type": "function"
        },
        {
            "id": "2",
            "content": "class UserService:\n    def get_user(self, user_id):\n        return self.repo.get_user(user_id)",
            "file_path": "app/services/user_service.py",
            "ast_type": "class"
        },
        {
            "id": "3",
            "content": "<div className=\"user-profile\">\n  <h1>{user.name}</h1>\n  <p>{user.email}</p>\n</div>",
            "file_path": "app/frontend/components/UserProfile.jsx",
            "ast_type": "component"
        },
        {
            "id": "4",
            "content": "import React from 'react';\nimport { UserProfile } from './components';\n\nexport const UserPage = ({ user }) => (\n  <div>\n    <UserProfile user={user} />\n  </div>\n);",
            "file_path": "app/frontend/pages/UserPage.jsx",
            "ast_type": "component"
        },
        {
            "id": "5",
            "content": "FROM python:3.9\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"python\", \"app.py\"]",
            "file_path": "Dockerfile",
            "ast_type": "config"
        }
    ]
    
    # Create a mock retriever that returns the mock chunks
    class MockRetriever:
        def get_chunks(self, query=None, project_id=None, k=20):
            return mock_chunks
    
    # Create a role-aware context injector with the mock retriever
    injector = RoleAwareContextInjector(role=role)
    injector.retriever = MockRetriever()
    
    # Inject relevant code chunks
    chunks = injector.inject(
        query=prompt,
        session_id="test-session",
        project_id="test-project"
    )
    
    # Format the chunks into a prompt
    formatter = ContextFormatter()
    prompt_with_context = formatter.create_prompt_with_context(
        prompt=prompt,
        chunks=chunks
    )
    
    # Print the prompt with context
    print("\n=== Prompt with Context ===\n")
    print(prompt_with_context)
    
    # Create an inference controller
    controller = InferenceController()
    
    # Check if Ollama is available
    try:
        response = controller.generate_response(
            prompt=prompt,
            session_id="test-session",
            project_id="test-project",
            role=role
        )
        
        print("\n=== Response ===\n")
        print(json.dumps(response, indent=2))
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        print("\n=== Error ===\n")
        print(f"Error generating response: {str(e)}")
        print("\nMake sure Ollama is running and the model is available.")

if __name__ == "__main__":
    main()
