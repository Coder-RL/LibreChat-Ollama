#!/usr/bin/env python3
"""
OpenSearch Initialization Module.
Provides application integration for OpenSearch with k-NN plugin.
"""

import os
import sys
import logging
import subprocess
from typing import Dict, Optional, Tuple, Union
import time

# Import our verification module
from opensearch_verification import OpenSearchVerifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('opensearch_initialization')

class OpenSearchInitializer:
    """
    Initializer for OpenSearch with k-NN plugin.
    Handles startup, verification, and graceful fallback.
    """
    
    def __init__(self, 
                 opensearch_dir: str = '/Users/robertlee/GitHubProjects/ollama-inference-app/opensearch',
                 connection_params: Optional[Dict] = None,
                 max_retries: int = 3,
                 retry_delay: int = 5):
        """
        Initialize with configuration parameters.
        
        Args:
            opensearch_dir: Directory containing OpenSearch Docker configuration
            connection_params: OpenSearch connection parameters
            max_retries: Maximum number of initialization retries
            retry_delay: Delay between retries in seconds
        """
        self.opensearch_dir = opensearch_dir
        self.connection_params = connection_params
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verifier = OpenSearchVerifier(connection_params)
        self.initialized = False
    
    def start_opensearch(self) -> bool:
        """
        Start OpenSearch using the enhanced start script.
        
        Returns:
            bool: True if OpenSearch started successfully, False otherwise
        """
        try:
            logger.info("Starting OpenSearch with k-NN plugin...")
            
            # Save current directory
            current_dir = os.getcwd()
            
            try:
                # Change to OpenSearch directory
                os.chdir(self.opensearch_dir)
                
                # Run the start script
                result = subprocess.run(
                    ['./start_opensearch.sh'],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Log script output
                for line in result.stdout.splitlines():
                    logger.info(f"OpenSearch startup: {line}")
                
                logger.info("OpenSearch startup script completed successfully")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"OpenSearch startup failed: {e}")
                logger.error(f"STDOUT: {e.stdout}")
                logger.error(f"STDERR: {e.stderr}")
                return False
            finally:
                # Restore previous directory
                os.chdir(current_dir)
                
        except Exception as e:
            logger.error(f"Error starting OpenSearch: {e}")
            return False
    
    def verify_opensearch(self) -> Tuple[bool, Dict]:
        """
        Verify OpenSearch is running correctly with k-NN plugin.
        
        Returns:
            Tuple[bool, Dict]: Success status and verification results
        """
        logger.info("Verifying OpenSearch with k-NN plugin...")
        return self.verifier.run_all_verifications()
    
    def initialize(self, auto_start: bool = True) -> bool:
        """
        Initialize OpenSearch with verification and retry logic.
        
        Args:
            auto_start: Whether to automatically start OpenSearch if needed
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("Initializing OpenSearch with k-NN plugin...")
        
        # First try verification without starting
        success, results = self.verify_opensearch()
        
        # If verification fails and auto_start is enabled, try starting and verifying
        if not success and auto_start:
            for attempt in range(1, self.max_retries + 1):
                logger.info(f"Initialization attempt {attempt}/{self.max_retries}")
                
                # Start OpenSearch
                start_success = self.start_opensearch()
                if not start_success:
                    logger.error(f"Failed to start OpenSearch (attempt {attempt}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue
                
                # Wait a bit for services to stabilize
                time.sleep(2)
                
                # Verify again
                success, results = self.verify_opensearch()
                
                if success:
                    logger.info("OpenSearch initialized successfully!")
                    break
                
                logger.error(f"Verification failed after starting OpenSearch (attempt {attempt}/{self.max_retries})")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
        
        self.initialized = success
        
        if success:
            logger.info("OpenSearch with k-NN plugin is ready for use")
        else:
            logger.error("Failed to initialize OpenSearch with k-NN plugin")
            
            # Provide specific error information
            for check_name, result in results.items():
                if not result["status"]:
                    logger.error(f"Failed check: {check_name}")
                    logger.error(f"Details: {result['details']}")
        
        return success
    
    def get_client(self):
        """
        Get the OpenSearch client if initialized.
        
        Returns:
            OpenSearch client or None if not initialized
        """
        if not self.initialized:
            logger.warning("OpenSearch not initialized. Call initialize() first.")
            return None
        
        return self.verifier.client

def main():
    """Run the initializer as a standalone script."""
    initializer = OpenSearchInitializer()
    success = initializer.initialize()
    
    # Return exit code based on success
    import sys
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()