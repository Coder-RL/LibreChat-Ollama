#!/usr/bin/env python3
"""
API interface for the InferenceController.
This script is called by the Node.js controller to generate responses.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Import the InferenceController
try:
    from controllers.inference_controller import InferenceController
except ImportError:
    # Add the parent directory to the path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.controllers.inference_controller import InferenceController

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate a response using the InferenceController')
    parser.add_argument('--prompt', required=True, help='The prompt to generate a response for')
    parser.add_argument('--session_id', default='default-session', help='The session identifier')
    parser.add_argument('--project_id', default='default-project', help='The project identifier')
    parser.add_argument('--role', default='default', help='The agent role')
    parser.add_argument('--model', help='The model to use for inference')
    parser.add_argument('--temperature', type=float, help='The temperature to use for generation')
    parser.add_argument('--max_tokens', type=int, help='The maximum number of tokens to generate')
    
    return parser.parse_args()

def format_chunk_for_output(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Format a chunk for output in the API response."""
    # Extract only the necessary fields to avoid serialization issues
    return {
        'file_path': chunk.get('file_path', ''),
        'ast_type': chunk.get('ast_type', ''),
        'chunk_type': chunk.get('chunk_type', ''),
        'name': chunk.get('name', ''),
        'score': chunk.get('score', 0),
        'content': chunk.get('content', '')[:500] + ('...' if len(chunk.get('content', '')) > 500 else '')
    }

def main() -> None:
    """Main function."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Initialize the controller
        controller_kwargs = {}
        if args.model:
            controller_kwargs['model'] = args.model
        
        controller = InferenceController(**controller_kwargs)
        
        # Generate response
        response_kwargs = {
            'prompt': args.prompt,
            'session_id': args.session_id,
            'project_id': args.project_id,
            'role': args.role
        }
        
        if args.temperature:
            response_kwargs['temperature'] = args.temperature
        
        if args.max_tokens:
            response_kwargs['max_tokens'] = args.max_tokens
        
        # Call the controller
        result = controller.generate_response(**response_kwargs)
        
        # Format the chunks for output
        if 'context' in result and isinstance(result['context'], list):
            result['context'] = [format_chunk_for_output(chunk) for chunk in result['context']]
        
        # Add debug information
        result['debug'] = {
            'chunks_retrieved': len(result.get('context', [])),
            'role': args.role,
            'model': controller.model
        }
        
        # Print the result as JSON to stdout
        print(json.dumps(result))
        
    except Exception as e:
        logger.exception(f"Error in inference_api.py: {str(e)}")
        error_result = {
            'success': False,
            'error': str(e),
            'response': f"Error occurred: {str(e)}"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == '__main__':
    main()
