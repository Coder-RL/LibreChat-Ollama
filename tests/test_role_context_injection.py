"""
Tests for the RoleAwareContextInjector.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.context.role_context_injector import RoleAwareContextInjector
from app.context.chunk_scorer import ChunkRelevanceScorer
from app.vector.chunk_retriever import ChunkRetriever

class TestRoleContextInjection(unittest.TestCase):
    """
    Tests for the RoleAwareContextInjector.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        # Create mock chunks for testing
        self.mock_chunks = [
            {
                "id": "1",
                "content": "def get_user(user_id):\n    return db.query(User).filter(User.id == user_id).first()",
                "file_path": "app/controllers/user_controller.py",
                "ast_type": "function",
                "embedding": np.random.rand(3072)
            },
            {
                "id": "2",
                "content": "class UserService:\n    def get_user(self, user_id):\n        return self.repo.get_user(user_id)",
                "file_path": "app/services/user_service.py",
                "ast_type": "class",
                "embedding": np.random.rand(3072)
            },
            {
                "id": "3",
                "content": "<div className=\"user-profile\">\n  <h1>{user.name}</h1>\n  <p>{user.email}</p>\n</div>",
                "file_path": "app/frontend/components/UserProfile.jsx",
                "ast_type": "component",
                "embedding": np.random.rand(3072)
            },
            {
                "id": "4",
                "content": "import React from 'react';\nimport { UserProfile } from './components';\n\nexport const UserPage = ({ user }) => (\n  <div>\n    <UserProfile user={user} />\n  </div>\n);",
                "file_path": "app/frontend/pages/UserPage.jsx",
                "ast_type": "component",
                "embedding": np.random.rand(3072)
            },
            {
                "id": "5",
                "content": "FROM python:3.9\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"python\", \"app.py\"]",
                "file_path": "Dockerfile",
                "ast_type": "config",
                "embedding": np.random.rand(3072)
            }
        ]

        # Create mock retriever
        self.mock_retriever = MagicMock(spec=ChunkRetriever)
        self.mock_retriever.get_chunks.return_value = self.mock_chunks
        self.mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create mock scorer
        self.mock_scorer = MagicMock(spec=ChunkRelevanceScorer)
        self.mock_scorer.score_chunks.return_value = sorted(
            self.mock_chunks,
            key=lambda c: c["id"],  # Sort by ID for predictable test results
            reverse=True
        )

    def test_backend_role_filtering(self):
        """
        Test that the backend role filters out frontend chunks.
        """
        # Create a custom retriever that returns the mock chunks
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.get_chunks.return_value = self.mock_chunks
        mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create a custom scorer that returns the chunks in the order they're given
        mock_scorer = MagicMock(spec=ChunkRelevanceScorer)
        mock_scorer.score_chunks = lambda query, chunks: sorted(chunks, key=lambda c: c["id"])

        # Create injector with backend role
        injector = RoleAwareContextInjector(
            role="backend",
            retriever=mock_retriever,
            scorer=mock_scorer
        )

        # Inject context
        result = injector.inject(
            prompt="How do I get a user?",
            project_id="test-project"
        )

        # Check that only backend chunks are included
        self.assertEqual(len(result), 2)
        self.assertIn("user_controller.py", result[0]["file_path"])
        self.assertIn("user_service.py", result[1]["file_path"])

    def test_frontend_role_filtering(self):
        """
        Test that the frontend role filters out backend chunks.
        """
        # Create a custom retriever that returns the mock chunks
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.get_chunks.return_value = self.mock_chunks
        mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create a custom scorer that returns the chunks in the order they're given
        mock_scorer = MagicMock(spec=ChunkRelevanceScorer)
        mock_scorer.score_chunks = lambda query, chunks: sorted(chunks, key=lambda c: c["id"])

        # Create injector with frontend role
        injector = RoleAwareContextInjector(
            role="frontend",
            retriever=mock_retriever,
            scorer=mock_scorer
        )

        # Inject context
        result = injector.inject(
            prompt="How do I display a user profile?",
            project_id="test-project"
        )

        # Check that only frontend chunks are included
        self.assertEqual(len(result), 2)
        self.assertIn("UserProfile.jsx", result[0]["file_path"])
        self.assertIn("UserPage.jsx", result[1]["file_path"])

    def test_refactor_role_keeps_all_chunks(self):
        """
        Test that the refactor role keeps all chunks.
        """
        # Create a custom retriever that returns the mock chunks
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.get_chunks.return_value = self.mock_chunks
        mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create a custom scorer that returns the chunks in the order they're given
        mock_scorer = MagicMock(spec=ChunkRelevanceScorer)
        mock_scorer.score_chunks = lambda query, chunks: sorted(chunks, key=lambda c: c["id"])

        # Create injector with refactor role
        injector = RoleAwareContextInjector(
            role="refactor",
            retriever=mock_retriever,
            scorer=mock_scorer
        )

        # Inject context
        result = injector.inject(
            prompt="Refactor the user code",
            project_id="test-project"
        )

        # Check that all chunks are included
        self.assertEqual(len(result), 5)

    def test_devops_role_filtering(self):
        """
        Test that the devops role filters appropriately.
        """
        # Create a custom retriever that returns the mock chunks
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.get_chunks.return_value = self.mock_chunks
        mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create a custom scorer that returns the chunks in the order they're given
        mock_scorer = MagicMock(spec=ChunkRelevanceScorer)
        mock_scorer.score_chunks = lambda query, chunks: sorted(chunks, key=lambda c: c["id"])

        # Create injector with devops role
        injector = RoleAwareContextInjector(
            role="devops",
            retriever=mock_retriever,
            scorer=mock_scorer
        )

        # Inject context
        result = injector.inject(
            prompt="How is the app deployed?",
            project_id="test-project"
        )

        # Check that only devops chunks are included
        self.assertEqual(len(result), 1)
        self.assertIn("Dockerfile", result[0]["file_path"])

    def test_chunk_scoring_order(self):
        """
        Test that chunks are ordered by score.
        """
        # Create a custom retriever that returns the mock chunks
        mock_retriever = MagicMock(spec=ChunkRetriever)
        mock_retriever.get_chunks.return_value = self.mock_chunks
        mock_retriever.retrieve_chunks.return_value = self.mock_chunks

        # Create a custom scorer that assigns predictable scores
        custom_scorer = MagicMock(spec=ChunkRelevanceScorer)

        # Create scored chunks with predictable scores
        scored_chunks = self.mock_chunks.copy()
        for i, chunk in enumerate(scored_chunks):
            chunk["score"] = 0.9 - (i * 0.1)  # Decreasing scores

        custom_scorer.score_chunks.return_value = scored_chunks

        # Create injector with custom scorer
        injector = RoleAwareContextInjector(
            role="default",
            retriever=mock_retriever,
            scorer=custom_scorer
        )

        # Inject context
        result = injector.inject(
            prompt="Test query",
            project_id="test-project"
        )

        # Check that chunks are ordered by score (descending)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["score"], 0.9)
        self.assertEqual(result[1]["score"], 0.8)
        self.assertEqual(result[2]["score"], 0.7)
        self.assertEqual(result[3]["score"], 0.6)
        self.assertEqual(result[4]["score"], 0.5)

    def test_ast_type_boosting(self):
        """
        Test that AST type boosting works correctly.
        """
        # Create a real scorer to test AST boosting
        real_scorer = ChunkRelevanceScorer()

        # Create chunks with the same content but different AST types
        chunks = [
            {
                "id": "1",
                "content": "def test_function():\n    return 'test'",
                "file_path": "test.py",
                "ast_type": "function",
                "embedding": np.ones(3072)  # Same embedding for all chunks
            },
            {
                "id": "2",
                "content": "def test_function():\n    return 'test'",
                "file_path": "test.py",
                "ast_type": "import",
                "embedding": np.ones(3072)
            },
            {
                "id": "3",
                "content": "def test_function():\n    return 'test'",
                "file_path": "test.py",
                "ast_type": "class",
                "embedding": np.ones(3072)
            }
        ]

        # Score the chunks
        scored_chunks = real_scorer.score_chunks("test function", chunks)

        # Check that function and class have higher scores than import
        self.assertGreater(
            next(c["score"] for c in scored_chunks if c["ast_type"] == "function"),
            next(c["score"] for c in scored_chunks if c["ast_type"] == "import")
        )
        self.assertGreater(
            next(c["score"] for c in scored_chunks if c["ast_type"] == "class"),
            next(c["score"] for c in scored_chunks if c["ast_type"] == "import")
        )

if __name__ == "__main__":
    unittest.main()
