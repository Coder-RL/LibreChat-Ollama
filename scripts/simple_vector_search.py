from opensearchpy import OpenSearch
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_vector_search')

def get_opensearch_client():
    """Create an OpenSearch client"""
    client = OpenSearch(
        hosts=[{'host': 'localhost', 'port': 9200}],
        http_auth=None,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )
    return client

def verify_opensearch():
    """Verify OpenSearch is running with k-NN plugin"""
    print("Running OpenSearch verification...")
    
    client = get_opensearch_client()
    
    # Step 1: Check connection
    try:
        info = client.info()
        print("✅ Connected to OpenSearch successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Step 2: Check cluster health
    health = client.cluster.health()
    status = health.get("status")
    print(f"✅ Cluster health: {status}")
    
    # Step 3: Check k-NN plugin
    plugins = client.cat.plugins(format="json")
    knn_plugins = [p for p in plugins if "knn" in p.get("name", "").lower()]
    
    if knn_plugins:
        plugin_version = knn_plugins[0].get("component")
        print(f"✅ k-NN plugin found (version: {plugin_version})")
    else:
        print("❌ k-NN plugin not found")
        return False
    
    # Step 4: Test k-NN index creation
    test_index = "test-simple-knn"
    
    try:
        # Delete index if it exists
        if client.indices.exists(index=test_index):
            client.indices.delete(index=test_index)
        
        # Create test index
        index_config = {
            "settings": {
                "index": {
                    "knn": True
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 4
                    }
                }
            }
        }
        
        client.indices.create(index=test_index, body=index_config)
        print("✅ Successfully created test k-NN index")
        
        # Clean up
        client.indices.delete(index=test_index)
        print("✅ Successfully deleted test k-NN index")
        
    except Exception as e:
        print(f"❌ k-NN index test failed: {e}")
        return False
    
    print("🎉 All verification checks passed!")
    return True

def basic_vector_search(query_vector, index_name, k=10):
    """
    Perform a basic vector search
    
    Args:
        query_vector (list): Vector to search for
        index_name (str): Name of the index to search
        k (int): Number of results to return
    
    Returns:
        list: Search results
    """
    client = get_opensearch_client()
    
    # Create the query
    query = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": k
                }
            }
        }
    }
    
    try:
        # Execute search
        response = client.search(index=index_name, body=query)
        
        # Format results
        results = []
        hits = response.get("hits", {}).get("hits", [])
        
        for hit in hits:
            results.append({
                "id": hit.get("_id"),
                "score": hit.get("_score"),
                "content": hit.get("_source")
            })
        
        logger.info(f"Found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

# Main function to run when the script is executed
if __name__ == "__main__":
    print("Simple Vector Search Utility")
    print("----------------------------")
    
    # Verify OpenSearch setup
    if verify_opensearch():
        print("\nOpenSearch verification passed. You can now use vector search functions.")
        
        # Example of how to use the search function
        print("\nExample usage:")
        print("  from simple_vector_search import basic_vector_search")
        print("  results = basic_vector_search([0.1, 0.2, 0.3, 0.4], 'your-index-name')")
        print("  print(results)")
    else:
        print("\nOpenSearch verification failed. Please check your setup.")