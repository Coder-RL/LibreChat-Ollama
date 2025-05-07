import requests
import json
import sys

def verify_opensearch():
    # Check basic connection
    try:
        response = requests.get("http://localhost:9200")
        print(f"✅ Connected to OpenSearch: {response.status_code}")
        print(f"Version: {json.loads(response.text).get('version', {}).get('number')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Check cluster health
    try:
        response = requests.get("http://localhost:9200/_cluster/health")
        health = json.loads(response.text)
        print(f"✅ Cluster health: {health.get('status')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Check plugins
    try:
        response = requests.get("http://localhost:9200/_cat/plugins?format=json")
        plugins = json.loads(response.text)
        plugin_names = [p.get('name', '') for p in plugins]
        
        print("Installed plugins:")
        for plugin in plugin_names:
            print(f"  - {plugin}")
        
        if any("knn" in plugin.lower() for plugin in plugin_names):
            print("✅ k-NN plugin is installed")
            return True
        else:
            print("❌ k-NN plugin NOT found")
            return False
    except Exception as e:
        print(f"❌ Plugin check failed: {e}")
        return False

if __name__ == "__main__":
    print("OpenSearch Verification")
    print("======================")
    success = verify_opensearch()
    sys.exit(0 if success else 1)