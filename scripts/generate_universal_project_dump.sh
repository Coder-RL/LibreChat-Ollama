#!/bin/bash

PROJECT_NAME=$(basename "$PWD")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${PROJECT_NAME}_dump_${TIMESTAMP}.md"

EXCLUDE_PATTERN='.*|node_modules|__pycache__|.venv|*.git|*.pyc|*.DS_Store|build'

INCLUDE_EXTENSIONS=( -name "*.py" -o -name "*.html" -o -name "*.json" -o -name "*.js" -o -name "*.ts" -o -name "*.css" -o -name "*.dart" -o -name "*.yaml" -o -name "*.yml" -o -name "*.gradle" -o -name "*.xml" )

rm -f "$OUTPUT_FILE"
echo "# Project Source Code Dump - ${PROJECT_NAME}" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Generated:** $(date)" >> "$OUTPUT_FILE"
echo "- **Directory:** $(pwd)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

tree -I "$EXCLUDE_PATTERN" > project_structure.txt
echo "## Project Structure" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
cat project_structure.txt >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
rm project_structure.txt

find . -type f "${INCLUDE_EXTENSIONS[@]}" ! -path "*/.*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" ! -path "*/.venv/*" ! -path "*/build/*" | sort > file_list.txt

echo "## Source Code" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

while IFS= read -r file
do
  echo "---" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "### \`$file\`" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "\`\`\`" >> "$OUTPUT_FILE"
  cat "$file" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "\`\`\`" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
done < file_list.txt

rm file_list.txt

echo "✅ Project dump complete: $OUTPUT_FILE"
