"""
Test the InferenceController.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.controllers.inference_controller import InferenceController
from app.context.role_context_injector import RoleAwareContextInjector
from app.context.context_formatter import ContextFormatter
from app.vector.chunk_retriever import ChunkRetriever
from app.context.chunk_scorer import ChunkRelevanceScorer

class TestInferenceController(unittest.TestCase):
    """
    Test the InferenceController.
    """

    def setUp(self):
        """
        Set up the test.
        """
        # Create mock chunks
        self.mock_chunks = [
            {
                "id": "1",
                "content": "def get_user(user_id):\n    return User.query.get(user_id)",
                "file_path": "app/controllers/user_controller.py",
                "ast_type": "function",
                "score": 0.8
            },
            {
                "id": "2",
                "content": "class UserService:\n    def get_user(self, user_id):\n        return User.query.get(user_id)",
                "file_path": "app/services/user_service.py",
                "ast_type": "class",
                "score": 0.9
            }
        ]

    @patch('requests.post')
    def test_generate_response_success(self, mock_post):
        """
        Test that generate_response returns a successful response.
        """
        # Mock the response from the Ollama API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response."
        }
        mock_post.return_value = mock_response

        # Create a mock ChunkRetriever
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create a mock RoleAwareContextInjector
        mock_injector = MagicMock(spec=RoleAwareContextInjector)
        mock_injector.inject.return_value = self.mock_chunks

        # Create a mock ContextFormatter
        mock_formatter = MagicMock(spec=ContextFormatter)
        mock_formatter.format_context.return_value = "Formatted context"

        # Create the controller with mocked dependencies
        controller = InferenceController()
        controller.chunk_retriever = mock_retriever
        
        # Patch the RoleAwareContextInjector constructor
        with patch('app.controllers.inference_controller.RoleAwareContextInjector', return_value=mock_injector):
            # Patch the ContextFormatter
            controller.formatter = mock_formatter
            
            # Call the method
            result = controller.generate_response(
                prompt="How do I get a user?",
                session_id="test-session",
                project_id="test-project",
                role="backend"
            )

            # Check the result
            self.assertTrue(result["success"])
            self.assertEqual(result["response"], "This is a test response.")
            self.assertEqual(len(result["context"]), 2)

    @patch('requests.post')
    def test_generate_response_no_chunks(self, mock_post):
        """
        Test that generate_response handles the case where no chunks are found.
        """
        # Create a mock ChunkRetriever that returns no chunks
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.retrieve_chunks.return_value = []

        # Create the controller with mocked dependencies
        controller = InferenceController()
        controller.chunk_retriever = mock_retriever

        # Call the method
        result = controller.generate_response(
            prompt="How do I get a user?",
            session_id="test-session",
            project_id="test-project",
            role="backend"
        )

        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["response"], "No relevant context found.")
        self.assertEqual(len(result["context"]), 0)

if __name__ == "__main__":
    unittest.main()
