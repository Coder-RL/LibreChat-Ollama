#!/bin/bash
# Block commits that contain files over 90MB

MAX_SIZE=$((90 * 1024 * 1024))  # 90MB

large_files=$(git diff --cached --name-only --diff-filter=AM | while read file; do
  if [ -f "$file" ]; then
    size=$(wc -c <"$file")
    if [ "$size" -gt "$MAX_SIZE" ]; then
      echo "$file ($(du -h "$file" | cut -f1))"
    fi
  fi
done)

if [ -n "$large_files" ]; then
  echo "❌ ERROR: The following files are too large to commit (over 90MB):"
  echo "$large_files"
  echo "🛑 Commit aborted. Consider using .gitignore or Git LFS."
  exit 1
fi

exit 0
