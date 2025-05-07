import os
import shutil
import uuid
import time
import requests
from pathlib import Path

# Configuration
SERVER_URL = "http://localhost:8050"  # Use the new port
API_ENDPOINT = f"{SERVER_URL}/api/ingest"
TEST_DIR = "/Users/robertlee/GitHubProjects/ollama-inference-app/test_comprehensive"
PROJECT_ID = str(uuid.uuid4())

# Create test directory structure
def setup_test_environment():
    print(f"Setting up test environment in {TEST_DIR}")

    # Clean up previous test directory if it exists
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

    # Create main test directory
    os.makedirs(TEST_DIR)

    # Create subdirectories
    os.makedirs(os.path.join(TEST_DIR, "python_files"))
    os.makedirs(os.path.join(TEST_DIR, "text_files"))
    os.makedirs(os.path.join(TEST_DIR, "empty_files"))
    os.makedirs(os.path.join(TEST_DIR, "large_files"))
    os.makedirs(os.path.join(TEST_DIR, "corrupted_files"))
    os.makedirs(os.path.join(TEST_DIR, "non_utf8_files"))

    # Create .gitignore file
    with open(os.path.join(TEST_DIR, ".gitignore"), "w") as f:
        f.write("# Ignore text files\n")
        f.write("*.txt\n")
        f.write("\n")
        f.write("# Ignore specific directory\n")
        f.write("ignored_dir/\n")

    # Create ignored directory
    os.makedirs(os.path.join(TEST_DIR, "ignored_dir"))
    with open(os.path.join(TEST_DIR, "ignored_dir", "ignored_file.py"), "w") as f:
        f.write("# This file should be ignored\n")

    # Create Python files with valid code
    with open(os.path.join(TEST_DIR, "python_files", "valid_file1.py"), "w") as f:
        f.write("""
def test_function():
    print("This is a test function")

class TestClass:
    def __init__(self):
        self.value = 42

    def test_method(self):
        print("This is a test method")
""")

    with open(os.path.join(TEST_DIR, "python_files", "valid_file2.py"), "w") as f:
        f.write("""
def another_function():
    print("This is another function")

class AnotherClass:
    def __init__(self, name):
        self.name = name

    def greet(self):
        print(f"Hello, {self.name}!")
""")

    # Create text files (should be ignored by gitignore)
    with open(os.path.join(TEST_DIR, "text_files", "text_file1.txt"), "w") as f:
        f.write("This is a text file that should be ignored by gitignore\n")

    with open(os.path.join(TEST_DIR, "text_files", "text_file2.txt"), "w") as f:
        f.write("This is another text file that should be ignored by gitignore\n")

    # Create empty files
    with open(os.path.join(TEST_DIR, "empty_files", "empty_file1.py"), "w") as f:
        f.write("")

    with open(os.path.join(TEST_DIR, "empty_files", "empty_file2.py"), "w") as f:
        f.write("   \n   \n")  # Only whitespace

    # Create large file (6MB)
    with open(os.path.join(TEST_DIR, "large_files", "large_file.py"), "w") as f:
        f.write("# This is a large file\n")
        f.write("x" * (6 * 1024 * 1024))  # 6MB of data

    # Create corrupted Python file
    with open(os.path.join(TEST_DIR, "corrupted_files", "corrupted_file.py"), "w") as f:
        f.write("""
def this_is_corrupted_syntax(
    print("Missing closing parenthesis"

class InvalidClass:
    def __init__(self)
        self.missing_colon = True
""")

    # Create non-UTF8 file
    with open(os.path.join(TEST_DIR, "non_utf8_files", "non_utf8_file.py"), "wb") as f:
        f.write(b"def test_function():\n")
        f.write(b"    print('This is a test function')\n\n")
        f.write(b"# \xff\xfe Invalid UTF-8 bytes \xff\xfe\n")
        f.write(b"class TestClass:\n")
        f.write(b"    def __init__(self):\n")
        f.write(b"        self.value = 42\n")

    print("Test environment setup complete")
    return TEST_DIR

# Test functions
def test_basic_ingestion():
    print("\n=== Test 1: Basic Ingestion - Valid Small Directory ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "python_files"),
            "project_id": PROJECT_ID,
            "gitignore_path": os.path.join(TEST_DIR, ".gitignore")
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ Basic ingestion test passed")
    else:
        print("❌ Basic ingestion test failed")

def test_gitignore_filtering():
    print("\n=== Test 2: Gitignore Filtering - Exclude Specific Files ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": TEST_DIR,
            "project_id": PROJECT_ID,
            "gitignore_path": os.path.join(TEST_DIR, ".gitignore")
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ Gitignore filtering test passed")
    else:
        print("❌ Gitignore filtering test failed")

def test_empty_files():
    print("\n=== Test 3: Skipped Files - Empty Files ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "empty_files"),
            "project_id": PROJECT_ID
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ Empty files test passed")
    else:
        print("❌ Empty files test failed")

def test_ast_parsing_failure():
    print("\n=== Test 4: AST Parsing Failure - Forced Error ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "corrupted_files"),
            "project_id": PROJECT_ID
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ AST parsing failure test passed")
    else:
        print("❌ AST parsing failure test failed")

def test_missing_directory():
    print("\n=== Test 5: Missing Directory Error ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "non_existent_directory"),
            "project_id": PROJECT_ID
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 400 and "does not exist" in response.text:
        print("✅ Missing directory test passed")
    else:
        print("❌ Missing directory test failed")

def test_large_file_handling():
    print("\n=== Test 6: Large File Handling ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "large_files"),
            "project_id": PROJECT_ID
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ Large file handling test passed")
    else:
        print("❌ Large file handling test failed")

def test_non_utf8_files():
    print("\n=== Test 7: Non-UTF8 Files ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "non_utf8_files"),
            "project_id": PROJECT_ID
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ Non-UTF8 files test passed")
    else:
        print("❌ Non-UTF8 files test failed")

def test_invalid_project_id():
    print("\n=== Test 8: Invalid Project ID ===")
    response = requests.post(
        API_ENDPOINT,
        json={
            "base_directory": os.path.join(TEST_DIR, "python_files"),
            "project_id": "invalid-project-id"
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 400 and "Invalid project_id format" in response.text:
        print("✅ Invalid project ID test passed")
    else:
        print("❌ Invalid project ID test failed")

# Main test runner
def run_tests():
    print(f"Starting comprehensive tests with project ID: {PROJECT_ID}")

    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/api/health")
        if response.status_code != 200:
            print(f"❌ Server not responding correctly at {SERVER_URL}")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {SERVER_URL}")
        return

    print(f"✅ Server is running at {SERVER_URL}")

    # Setup test environment
    setup_test_environment()

    # Run tests
    test_basic_ingestion()
    test_gitignore_filtering()
    test_empty_files()
    test_ast_parsing_failure()
    test_missing_directory()
    test_large_file_handling()
    test_non_utf8_files()
    test_invalid_project_id()

    print("\n=== Test Summary ===")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Test directory: {TEST_DIR}")
    print("All tests completed")

if __name__ == "__main__":
    run_tests()
