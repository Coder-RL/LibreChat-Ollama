#!/usr/bin/env python3
"""
OpenSearch Verification Module.
Provides comprehensive verification of OpenSearch with k-NN plugin.
Can be imported and used programmatically in your application.
"""

import json
import logging
import time
from typing import Dict, List, Tuple, Union, Optional
from opensearchpy import OpenSearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('opensearch_verification')

# OpenSearch connection parameters
OS_PARAMS = {
    'hosts': [{'host': 'localhost', 'port': 9200}],
    'http_auth': None,  # No auth for development setup
    'use_ssl': False,
    'verify_certs': False,
    'ssl_assert_hostname': False,
    'ssl_show_warn': False
}

class OpenSearchVerifier:
    """OpenSearch verification utility with detailed testing capabilities."""
    
    def __init__(self, connection_params: Optional[Dict] = None):
        """
        Initialize the verifier with connection parameters.
        
        Args:
            connection_params: OpenSearch connection parameters (optional)
        """
        self.connection_params = connection_params or OS_PARAMS
        self.client = None
        self.verification_results = {
            "http_connection": {"status": False, "details": None},
            "cluster_health": {"status": False, "details": None},
            "knn_plugin": {"status": False, "details": None},
            "knn_index_test": {"status": False, "details": None}
        }
    
    def connect(self) -> bool:
        """
        Connect to OpenSearch.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = OpenSearch(**self.connection_params)
            response = self.client.info()
            self.verification_results["http_connection"] = {
                "status": True,
                "details": {
                    "version": response.get("version", {}).get("number", "Unknown"),
                    "cluster_name": response.get("cluster_name", "Unknown")
                }
            }
            logger.info(f"Successfully connected to OpenSearch {response.get('version', {}).get('number', 'Unknown')}")
            return True
        except Exception as e:
            self.verification_results["http_connection"] = {
                "status": False,
                "details": str(e)
            }
            logger.error(f"Failed to connect to OpenSearch: {e}")
            return False
    
    def check_cluster_health(self) -> bool:
        """
        Check OpenSearch cluster health.
        
        Returns:
            bool: True if cluster health is green or yellow, False otherwise
        """
        if not self.client:
            logger.error("No OpenSearch connection. Call connect() first.")
            return False
        
        try:
            health = self.client.cluster.health()
            status = health.get("status")
            self.verification_results["cluster_health"] = {
                "status": status in ["green", "yellow"],
                "details": {
                    "status": status,
                    "number_of_nodes": health.get("number_of_nodes"),
                    "active_shards_percent": health.get("active_shards_percent"),
                    "unassigned_shards": health.get("unassigned_shards")
                }
            }
            
            logger.info(f"Cluster health: {status}")
            return status in ["green", "yellow"]
        except Exception as e:
            self.verification_results["cluster_health"] = {
                "status": False,
                "details": str(e)
            }
            logger.error(f"Failed to check cluster health: {e}")
            return False
    
    def check_knn_plugin(self) -> bool:
        """
        Check if k-NN plugin is installed.
        
        Returns:
            bool: True if k-NN plugin is installed, False otherwise
        """
        if not self.client:
            logger.error("No OpenSearch connection. Call connect() first.")
            return False
        
        try:
            plugins = self.client.cat.plugins(format="json")
            knn_plugins = [p for p in plugins if p.get("name", "").lower() == "opensearch-knn"]
            
            if knn_plugins:
                plugin_details = knn_plugins[0]
                self.verification_results["knn_plugin"] = {
                    "status": True,
                    "details": {
                        "version": plugin_details.get("component"),
                        "node": plugin_details.get("node")
                    }
                }
                logger.info(f"k-NN plugin found (version: {plugin_details.get('component')})")
                return True
            else:
                self.verification_results["knn_plugin"] = {
                    "status": False,
                    "details": "k-NN plugin not found"
                }
                logger.error("k-NN plugin not found")
                return False
        except Exception as e:
            self.verification_results["knn_plugin"] = {
                "status": False,
                "details": str(e)
            }
            logger.error(f"Failed to check k-NN plugin: {e}")
            return False
    
    def test_knn_index(self) -> bool:
        """
        Test k-NN index creation, indexing and search.
        
        Returns:
            bool: True if k-NN index test is successful, False otherwise
        """
        if not self.client:
            logger.error("No OpenSearch connection. Call connect() first.")
            return False
        
        test_index_name = "test-knn-verification"
        try:
            # Delete test index if it exists
            if self.client.indices.exists(index=test_index_name):
                self.client.indices.delete(index=test_index_name)
                logger.info(f"Deleted existing test index {test_index_name}")
            
            # Create test index with k-NN enabled
            index_config = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                },
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 4  # Small dimension for testing
                        },
                        "text": {
                            "type": "text"
                        }
                    }
                }
            }
            
            # Create index
            create_result = self.client.indices.create(index=test_index_name, body=index_config)
            
            if not create_result.get("acknowledged", False):
                raise Exception("Index creation not acknowledged")
            
            logger.info(f"Created test index {test_index_name}")
            
            # Insert test document
            test_doc = {
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "text": "Test document"
            }
            
            index_result = self.client.index(
                index=test_index_name,
                id=1,
                body=test_doc,
                refresh=True
            )
            
            if not index_result.get("_shards", {}).get("successful", 0) > 0:
                raise Exception("Document indexing failed")
            
            logger.info("Indexed test document")
            
            # Perform k-NN search
            query = {
                "size": 1,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": [0.1, 0.2, 0.3, 0.4],
                            "k": 1
                        }
                    }
                }
            }
            
            search_result = self.client.search(
                index=test_index_name,
                body=query
            )
            
            hits = search_result.get("hits", {}).get("hits", [])
            if not hits:
                raise Exception("k-NN search returned no results")
            
            logger.info(f"k-NN search successful, found {len(hits)} results")
            
            self.verification_results["knn_index_test"] = {
                "status": True,
                "details": {
                    "index_creation": create_result.get("acknowledged"),
                    "document_indexing": index_result.get("result"),
                    "search_results": len(hits)
                }
            }
            
            return True
        except Exception as e:
            self.verification_results["knn_index_test"] = {
                "status": False,
                "details": str(e)
            }
            logger.error(f"k-NN index test failed: {e}")
            return False
        finally:
            # Clean up - delete test index
            try:
                if self.client.indices.exists(index=test_index_name):
                    self.client.indices.delete(index=test_index_name)
                    logger.info(f"Cleaned up test index {test_index_name}")
            except Exception as e:
                logger.error(f"Failed to clean up test index: {e}")
    
    def run_all_verifications(self) -> Tuple[bool, Dict]:
        """
        Run all verification tests.
        
        Returns:
            Tuple[bool, Dict]: Overall success status and detailed results
        """
        # Connect to OpenSearch
        connection_success = self.connect()
        if not connection_success:
            return False, self.verification_results
        
        # Check cluster health
        health_success = self.check_cluster_health()
        
        # Check k-NN plugin
        plugin_success = self.check_knn_plugin()
        
        # Test k-NN index
        index_test_success = False
        if plugin_success:
            index_test_success = self.test_knn_index()
        
        # Overall success if all critical checks pass
        overall_success = connection_success and health_success and plugin_success and index_test_success
        
        # Print summary
        self._print_verification_summary()
        
        return overall_success, self.verification_results
    
    def _print_verification_summary(self):
        """Print a summary of the verification results."""
        logger.info("=== OpenSearch Verification Summary ===")
        
        for check_name, result in self.verification_results.items():
            status = "✅ PASS" if result["status"] else "❌ FAIL"
            logger.info(f"{status} - {check_name}")
            
            if isinstance(result["details"], dict):
                for key, value in result["details"].items():
                    logger.info(f"  - {key}: {value}")
            elif result["details"]:
                logger.info(f"  - {result['details']}")
        
        all_passed = all(result["status"] for result in self.verification_results.values())
        if all_passed:
            logger.info("✅ All verification checks PASSED!")
        else:
            logger.info("❌ Some verification checks FAILED!")

def main():
    """Run the verifier as a standalone script."""
    verifier = OpenSearchVerifier()
    success, results = verifier.run_all_verifications()
    
    # Return exit code based on success
    import sys
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()