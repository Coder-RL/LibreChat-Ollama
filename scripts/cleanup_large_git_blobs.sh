#!/bin/bash

# FILE: cleanup_large_git_blobs.sh
# PURPOSE: Safely strip large blobs from Git history, clean repo, and push to GitHub.
# ⚠️ USE THIS SCRIPT ONLY IF YOU FULLY UNDERSTAND THE CONSEQUENCES OF REWRITING GIT HISTORY

# === Step 1: Set up variables ===
THRESHOLD_MB=100
BFG_JAR="bfg-1.15.0.jar"  # Assumes BFG is downloaded to this path
REPO_PATH=$(pwd)
MAX_SIZE_BYTES=$((THRESHOLD_MB * 1024 * 1024))

echo "🧹 Starting Git cleanup for repository at: $REPO_PATH"

# === Step 2: Find large blobs (over threshold) ===
echo "🔍 Scanning for blobs > ${THRESHOLD_MB}MB..."
mkdir -p .git/tmp
git verify-pack -v .git/objects/pack/pack-*.idx | \
  sort -k 3 -n | \
  awk -v max=$MAX_SIZE_BYTES '$3 > max { print $1, $3 }' > .git/tmp/large-blobs.txt

if [[ ! -s .git/tmp/large-blobs.txt ]]; then
  echo "✅ No large blobs found over ${THRESHOLD_MB}MB."
  exit 0
fi

# === Step 3: Extract blob IDs ===
cut -d' ' -f1 .git/tmp/large-blobs.txt > blobids.txt
echo "🧾 Found $(wc -l < blobids.txt) large blob(s) over ${THRESHOLD_MB}MB"

# === Step 4: Run BFG to strip blobs ===
if [[ ! -f "$BFG_JAR" ]]; then
  echo "❌ BFG JAR not found: $BFG_JAR"
  echo "Download from: https://rtyley.github.io/bfg-repo-cleaner/"
  exit 1
fi

echo "🧨 Stripping blobs with BFG..."
java -jar "$BFG_JAR" --strip-blobs-with-ids blobids.txt

# === Step 5: Cleanup with reflog & GC ===
echo "🗑️ Running garbage collection..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# === Step 6: Force push to GitHub ===
echo "🚀 Force pushing clean history to origin/main..."
git push origin main --force

# === Step 7: Cleanup ===
rm -rf .git/tmp blobids.txt

echo "✅ Cleanup complete! Repo has been rewritten and synced."
