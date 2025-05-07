from simple_vector_search import basic_vector_search, verify_opensearch

# First verify OpenSearch is running correctly
if not verify_opensearch():
    print("OpenSearch verification failed. Please check your setup.")
    exit(1)

# Example query vector (this would normally come from an embedding model)
query_vector = [0.1, 0.2, 0.3, 0.4]

# You would replace "your-index-name" with the actual index you want to search
# This is just a placeholder example
print("\nExample search (note: this will only work if you have created an index with vectors):")
print(f"Searching with vector: {query_vector}")

try:
    # This is just a demonstration - it will likely fail unless you've already
    # created an index with vector data
    results = basic_vector_search(
        query_vector=query_vector, 
        index_name="test-index",  # Replace with your actual index name
        k=5  # Return top 5 results
    )
    
    if results:
        print(f"Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  ID: {result['id']}")
            print(f"  Score: {result['score']}")
            print(f"  Content: {result['content']}")
    else:
        print("No results found or index doesn't exist")
        
except Exception as e:
    print(f"Search example failed: {e}")
    print("This is expected if you haven't created an index with vector data yet.")
    
print("\nNext steps:")
print("1. Create an index with vector data")
print("2. Index some documents with vector embeddings")
print("3. Run vector searches against your data")