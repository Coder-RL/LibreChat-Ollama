import os

# Create a large file (6MB)
large_file_path = "/Users/robertlee/GitHubProjects/ollama-inference-app/test_dir/large_file.txt"
with open(large_file_path, "w") as f:
    # Write 6MB of data (6 * 1024 * 1024 bytes)
    f.write("x" * (6 * 1024 * 1024))

print(f"Created large file: {large_file_path}")
print(f"File size: {os.path.getsize(large_file_path) / (1024 * 1024):.2f} MB")
