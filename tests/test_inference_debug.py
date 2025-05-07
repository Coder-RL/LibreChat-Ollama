#!/usr/bin/env python3
"""
E2E debug test script to validate real inference flow with detailed logging.
"""

import os
import sys
import uuid
import json
import time
import argparse
import requests
from typing import Dict, Any, Optional

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('inference_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
BASE_URL = "http://localhost:8000/api/ollama/chat"
MODEL_NAME = "deepseek-coder:6.7b"  # Adjust to match your available Ollama model
HTTP_TIMEOUT = 60  # seconds

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test the inference flow')
    parser.add_argument('--url', default=BASE_URL, help='The API endpoint URL')
    parser.add_argument('--model', default=MODEL_NAME, help='The model to use')
    parser.add_argument('--role', default='frontend', help='The agent role')
    parser.add_argument('--prompt', default='What does the main React component do in this codebase?', 
                       help='The prompt to test with')
    parser.add_argument('--timeout', type=int, default=HTTP_TIMEOUT, help='HTTP request timeout in seconds')
    
    return parser.parse_args()

def check_services() -> bool:
    """Check if required services are running."""
    logger.info("Checking if required services are running...")
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Ollama is not running or not responding")
            return False
        logger.info("✅ Ollama is running")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Ollama: {str(e)}")
        return False
    
    # Check if the API server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ API server is not running or not responding")
            return False
        logger.info("✅ API server is running")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to API server: {str(e)}")
        return False
    
    return True

def test_inference_flow(args: argparse.Namespace) -> None:
    """Test the inference flow."""
    logger.info("🔍 Testing inference flow...")
    
    # Generate unique IDs for the test
    session_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    
    # Prepare the payload
    payload = {
        "session_id": session_id,
        "project_id": project_id,
        "role": args.role,
        "prompt": args.prompt,
        "model": args.model
    }
    
    logger.info(f"📤 Sending request to {args.url}")
    logger.info(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send the request
        start_time = time.time()
        response = requests.post(args.url, json=payload, timeout=args.timeout)
        elapsed_time = time.time() - start_time
        
        # Log the response status
        logger.info(f"📥 Response status: {response.status_code} (took {elapsed_time:.2f}s)")
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"❌ HTTP {response.status_code}: {response.text}")
            sys.exit(1)
        
        # Parse the response
        data = response.json()
        
        # Check if the response was successful
        if not data.get("success", False):
            logger.error(f"❌ API response indicates failure: {data.get('error', 'Unknown error')}")
            sys.exit(1)
        
        logger.info("✅ API call succeeded")
        
        # Log the response data
        logger.info("📦 Raw JSON Response:")
        logger.info(json.dumps(data, indent=2))
        
        # Parse useful debug metadata
        logger.info("--- Debug Summary ---")
        context = data.get("context", [])
        
        if context:
            logger.info(f"📌 Chunks Retrieved ({len(context)}):")
            for i, c in enumerate(context):
                logger.info(f"  [{i+1}] {c.get('file_path')} | AST: {c.get('ast_type', c.get('chunk_type', 'unknown'))}")
        
        # Log the model response
        logger.info("🧠 Model Response:")
        logger.info(data.get("response", "").strip())
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error sending request: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Main function."""
    print("\n🔍 LibreChat-Ollama Inference Debug Test\n")
    
    # Parse arguments
    args = parse_arguments()
    
    # Check if required services are running
    if not check_services():
        logger.error("❌ Required services are not running. Aborting test.")
        sys.exit(1)
    
    # Test the inference flow
    test_inference_flow(args)
    
    print("\n✅ Test completed successfully. See inference_debug.log for details.\n")

if __name__ == "__main__":
    main()
