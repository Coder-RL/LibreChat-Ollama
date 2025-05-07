import os

# Create a file with non-UTF8 characters
non_utf8_file_path = "/Users/robertlee/GitHubProjects/ollama-inference-app/test_dir/non_utf8_file.py"
with open(non_utf8_file_path, "wb") as f:
    # Write some valid Python code
    f.write(b"def test_function():\n")
    f.write(b"    print('This is a test function')\n\n")
    
    # Write some invalid UTF-8 bytes
    f.write(b"# \xff\xfe Invalid UTF-8 bytes \xff\xfe\n")
    
    # Write more valid Python code
    f.write(b"class TestClass:\n")
    f.write(b"    def __init__(self):\n")
    f.write(b"        self.value = 42\n")

print(f"Created non-UTF8 file: {non_utf8_file_path}")
