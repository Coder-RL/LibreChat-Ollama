#!/bin/bash

# Set output filename
OUTPUT_FILE="project_dump.md"

# Set exclusions
EXCLUDE_PATTERN='.*|node_modules|__pycache__|.venv|*.git|*.pyc|*.DS_Store'

# Start fresh
rm -f "$OUTPUT_FILE"
echo "# Project Source Code Dump" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Dump project tree structure
tree -I "$EXCLUDE_PATTERN" > project_structure.txt
cat project_structure.txt >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
rm project_structure.txt

# Find all important source files
find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.json" -o -name "*.js" \) ! -path "*/.*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" ! -path "*/.venv/*" | sort > file_list.txt

# Dump each file's content
while IFS= read -r file
do
  echo "" >> "$OUTPUT_FILE"
  echo "---" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "### \`$file\`" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "\`\`\`" >> "$OUTPUT_FILE"
  cat "$file" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "\`\`\`" >> "$OUTPUT_FILE"
done < file_list.txt

# Cleanup
rm file_list.txt

echo "✅ Project dump complete: $OUTPUT_FILE"
